#!/usr/bin/env python3
"""Zoe: a wake-word voice assistant that pulls things up on screen.

Say "Hey Zoe" then a request. She opens what you ask for in your browser (the news,
a YouTube search, a Google search, a site) and confirms out loud. Her live HUD opens
when she starts. No push-to-talk: she is always listening for her name.

Pipeline: mic (voice-activity) -> Deepgram (hear) -> wake word -> Groq (decide what to
open) -> browser opens it + ElevenLabs (Lily) speaks.

  python tools/zoe_assistant.py     (or run zoe.bat, which also starts the HUD)
"""
import os, sys, io, json, time, wave, queue, subprocess, urllib.request, webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_speak import load_env, tts, play

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 16000
RMS_THRESHOLD = 600        # mic sensitivity; lower = picks up quieter speech. Tune if needed.
WAKE_WORDS = ("zoe", "zoey", "zo", "hey zoe", "ok zoe")
GROQ_MODEL = "llama-3.3-70b-versatile"

INTENT_SYS = (
    "You are Zoe's command router on Chris's Windows PC. Reply with ONLY a JSON object: "
    '{"action": "workspace|launch|folder|web|chat", "target": "", "url": "", "say": ""}. '
    "- workspace: he wants to start a named workspace or mode (coding, school, gaming, editing). "
    "target = the workspace name or his exact phrase. "
    "- launch: open a desktop app. target = the app name, e.g. Discord, Spotify, VS Code, Notepad. "
    "- folder: open a folder. target = a Windows path; map Downloads, Documents, Desktop, Videos, "
    "Pictures, Music to %USERPROFILE%\\\\<name>. "
    "- web: see, show, pull up, search, watch, or look something up. url = the best https URL "
    "(news -> https://news.google.com ; youtube -> https://www.youtube.com/results?search_query=QUERY ; "
    "otherwise https://www.google.com/search?q=QUERY, URL-encoded). "
    "- chat: plain conversation. "
    "Always set say to one short spoken sentence, address him as sir or Chris."
)

def post_control(base, route, payload):
    try:
        req = urllib.request.Request(base.rstrip('/') + route,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.load(r)
    except Exception:
        return None

def groq(messages, key, max_tokens=200):
    body = json.dumps({"model": GROQ_MODEL, "messages": messages,
                       "max_tokens": max_tokens, "temperature": 0.5}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "curl/8.19.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

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
    miss = [n for n, v in [("GROQ_API_KEY", groq_key), ("DEEPGRAM_API_KEY", dg),
                           ("ELEVENLABS_API_KEY", el), ("ELEVENLABS_VOICE_ID", voice)] if not v]
    if miss:
        sys.exit("missing in .env: " + ", ".join(miss))

    def speak(s):
        try: play(tts(s, el, voice))
        except Exception as e: print("  (speak error:", e, ")")

    boot_hud()
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
            low = text.lower()
            if not any(w in low for w in WAKE_WORDS):
                continue  # not addressed to Zoe
            print("  heard:  ", text)
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
                raw = groq([{"role": "system", "content": INTENT_SYS}] + history[-4:]
                           + [{"role": "user", "content": command}], groq_key)
                intent = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
            except Exception as e:
                print("  intent error:", e); speak("Sorry sir, I didn't catch that."); continue
            action = intent.get("action", "chat")
            target = intent.get("target", "")
            url = intent.get("url", "")
            say = intent.get("say", "On it, sir.")
            ctrl = os.environ.get("ZOE_CONTROL")   # set by the Electron app
            print(f"  intent: {action} {target or url}")
            if action == "workspace":
                post_control(ctrl, "/voice", {"phrase": target or command}) if ctrl else None
            elif action == "launch":
                if not (ctrl and post_control(ctrl, "/action", {"launch": target})) and target:
                    try: subprocess.Popen(["cmd", "/c", "start", "", target])
                    except Exception: pass
            elif action == "folder":
                if not (ctrl and post_control(ctrl, "/action", {"folder": target})):
                    p = os.path.expandvars(target)
                    if p and os.path.exists(p):
                        try: os.startfile(p)
                        except Exception: pass
            elif action == "web" and isinstance(url, str) and url.startswith(("http://", "https://")):
                webbrowser.open(url)
            history += [{"role": "user", "content": command},
                        {"role": "assistant", "content": say}]
            history = history[-8:]
            print("  ZOE:    ", say, "\n")
            speak(say)
    except KeyboardInterrupt:
        print("\n  Zoe offline. Goodbye, sir.\n")

if __name__ == "__main__":
    main()
