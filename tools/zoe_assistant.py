#!/usr/bin/env python3
"""Zoe: a wake-word voice assistant. The ears, mouth, and wake word.

Say "Hey Zoe" then a request. This script only does audio: capture (voice-activity),
transcribe (Deepgram), pass the command to zoe_router (the ONE place command meaning and
dispatch live), then speak the reply (ElevenLabs). It does not decide what commands mean;
zoe_router does. See COMMAND_SYSTEM_GUIDE.md.

  python tools/zoe_assistant.py     (or the Electron app starts it for you)
"""
import os, sys, io, json, time, wave, queue, subprocess, urllib.request, webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_speak import load_env, tts, play
import zoe_router   # the single command router (classify + dispatch)
import zoe_state    # persistent continuity (memory/zoe_state.json), best-effort
import zoe_memory   # Obsidian long-term memory vault, best-effort

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 16000
RMS_THRESHOLD = 600        # mic sensitivity; lower = picks up quieter speech. Tune if needed.
WAKE_WORDS = ("zoe", "zoey", "zo", "hey zoe", "ok zoe")

def calibrate_threshold():
    """Pick the wake (mic) threshold so Zoe hears your voice but not silence. ZOE_MIC_THRESHOLD
    wins if set; otherwise sample ~1.2s of room noise and set the bar just above it. Bounded
    [250, 1500], best-effort (falls back to 600 if there is no mic)."""
    env = os.environ.get("ZOE_MIC_THRESHOLD")
    if env:
        try: return max(50, int(env))
        except ValueError: pass
    try:
        import sounddevice as sd, numpy as np
        q = queue.Queue()
        with sd.InputStream(samplerate=SR, channels=1, dtype="int16",
                            blocksize=int(SR * 0.05), callback=lambda i, n, t, s: q.put(i.copy())):
            vals, start = [], time.time()
            while time.time() - start < 1.2:
                try: b = q.get(timeout=0.5)
                except queue.Empty: continue
                vals.append(float(np.sqrt(np.mean(b.astype(np.float32) ** 2))))
        if vals:
            vals.sort()
            ambient = vals[len(vals) // 2]            # median room noise
            return int(min(max(ambient * 2.5, 250), 1500))
    except Exception:
        pass
    return 600

def listen_utterance(max_wait=None):
    """Record one spoken utterance using simple energy voice-activity detection."""
    import sounddevice as sd, numpy as np
    q = queue.Queue()
    frames, speaking, silence, started = [], False, 0.0, time.time()
    with sd.InputStream(samplerate=SR, channels=1, dtype="int16",
                        blocksize=int(SR * 0.05), callback=lambda i, n, t, s: q.put(i.copy())):
        while True:
            try:
                block = q.get(timeout=1)
            except queue.Empty:
                if max_wait and time.time() - started > max_wait:
                    return None
                continue
            rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))
            if rms > RMS_THRESHOLD:
                speaking = True; silence = 0.0; frames.append(block)
            elif speaking:
                frames.append(block); silence += 0.05
                if silence > 0.9:
                    break
            if max_wait and not speaking and time.time() - started > max_wait:
                return None
    import numpy as np
    return np.concatenate(frames, axis=0) if frames else None

def to_wav(audio):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    return buf.getvalue()

def stt(wav_bytes, key):
    req = urllib.request.Request(
        "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&punctuate=true",
        data=wav_bytes, headers={"Authorization": f"Token {key}", "Content-Type": "audio/wav"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return d["results"]["channels"][0]["alternatives"][0]["transcript"].strip()

def strip_wake(text):
    t = text.lower().strip(" ,.!?")
    for w in ("hey zoe", "ok zoe", "okay zoe", "zoey", "zoe"):
        if t.startswith(w):
            return text.strip()[len(w):].strip(" ,.!?")
    return ""

def summon_ui(ctrl):
    """Wake word heard -> ask the Electron app to bring Zoe's window to the front. Best-effort:
    does nothing when running standalone (no Electron control endpoint), never blocks listening."""
    if not ctrl:
        return
    try:
        req = urllib.request.Request(ctrl.rstrip("/") + "/wake", data=b"{}",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass

def boot_hud():
    """Make sure the telemetry HUD is up, then open it (Zoe's visual presence)."""
    try:
        urllib.request.urlopen("http://localhost:7717/stats", timeout=0.6)
    except Exception:
        subprocess.Popen([sys.executable, os.path.join(ROOT, "tools", "zoe_server.py")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.5)
    webbrowser.open("http://localhost:7717")

def main():
    load_env()
    groq_key = os.environ.get("GROQ_API_KEY")
    dg = os.environ.get("DEEPGRAM_API_KEY")
    el = os.environ.get("ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVENLABS_VOICE_ID")
    ctrl = os.environ.get("ZOE_CONTROL")   # set by the Electron app; None when standalone
    miss = [n for n, v in [("GROQ_API_KEY", groq_key), ("DEEPGRAM_API_KEY", dg),
                           ("ELEVENLABS_API_KEY", el), ("ELEVENLABS_VOICE_ID", voice)] if not v]
    if miss:
        sys.exit("missing in .env: " + ", ".join(miss))

    def speak(s):
        try: play(tts(s, el, voice))
        except Exception as e: print("  (speak error:", e, ")")

    # persistent continuity: detect mode and restore the prior session (best-effort)
    try:
        urllib.request.urlopen("http://localhost:7717/stats", timeout=0.8)
        zoe_state.set_mode("online")
    except Exception:
        zoe_state.set_mode("offline")
    prior = zoe_state.start_session(context="voice session").get("last_commands", [])
    if prior:
        print(f"  restored session: {len(prior)} prior command(s), last = {prior[-1].get('text','')!r}")

    # Only open the HUD here when running standalone. Under Electron the app owns the window.
    if not ctrl:
        boot_hud()
    # auto-calibrate the mic to the room so Zoe hears your voice without you tuning anything
    global RMS_THRESHOLD
    RMS_THRESHOLD = calibrate_threshold()
    print(f"  mic wake threshold: {RMS_THRESHOLD}  (set ZOE_MIC_THRESHOLD in .env to override)")
    print("\n  ZOE is listening. Say 'Hey Zoe' then your request. Ctrl+C to quit.\n")
    speak("Zoe online, sir. Say hey Zoe whenever you need me.")
    history = []
    try:
        while True:
            audio = listen_utterance()
            if audio is None or len(audio) < SR * 0.3:
                continue
            try:
                text = stt(to_wav(audio), dg)
            except Exception as e:
                print("  stt error:", e); continue
            if not text:
                continue
            if not any(w in text.lower() for w in WAKE_WORDS):
                continue  # not addressed to Zoe
            print("  heard:  ", text)
            summon_ui(ctrl)   # "hey zoe" -> pop the window to the front
            command = strip_wake(text)
            if not command:
                speak("Yes, sir?")
                audio = listen_utterance(max_wait=6)
                if audio is None:
                    continue
                try: command = stt(to_wav(audio), dg)
                except Exception: continue
            if not command:
                continue
            print("  command:", command)
            try:
                say, act = zoe_router.handle(command, groq_key, ctrl, history)
            except Exception as e:
                print("  router error:", e); speak("Sorry sir, something went wrong."); continue
            print(f"  intent: {act} | ZOE: {say}\n")
            history += [{"role": "user", "content": command},
                        {"role": "assistant", "content": say}]
            history = history[-8:]
            speak(say)
    except KeyboardInterrupt:
        zoe_state.save(zoe_state.load())   # preserve continuity on shutdown
        try: zoe_memory.sync()             # snapshot this session into the Obsidian vault
        except Exception: pass
        print("\n  Zoe offline. Goodbye, sir.\n")

if __name__ == "__main__":
    main()
