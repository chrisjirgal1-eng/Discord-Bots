#!/usr/bin/env python3
"""JARVIS talk-back: turn text into speech in JARVIS's voice and play it.

Reads ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID from .env, calls ElevenLabs TTS,
and plays the audio. Voice-agnostic: whatever ELEVENLABS_VOICE_ID is set to is what
she speaks in, so it auto-uses the upgrade pick once the account is on Creator tier.

Usage:
  python tools/jarvis_speak.py "Wide awake, sir. What shall we build today?"
  echo "text" | python tools/jarvis_speak.py        # reads stdin if no arg
"""
import os, sys, json, tempfile, subprocess, urllib.request, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "eleven_flash_v2_5"  # ~75ms model latency, 2-4x faster than turbo
PCM_SR = 24000               # ElevenLabs pcm_24000 stream: raw 16-bit mono @ 24kHz

def load_env():
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def tts(text, key, voice_id):
    body = json.dumps({"text": text, "model_id": MODEL,
                       "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", data=body,
        headers={"xi-api-key": key, "Content-Type": "application/json",
                 "Accept": "audio/mpeg", "User-Agent": "curl/8.19.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

# ---- streaming path (the latency fix) ---------------------------------------
# Stream raw PCM straight to the speaker so the first word plays in ~150-400ms
# instead of waiting 1-3s for the whole MP3. Playback runs on a worker thread so
# the listen loop is never frozen, and a stop flag lets a new utterance cut in.

def _gain_factor():
    """ZOE_VOICE_GAIN is in dB (default +4); convert to a linear multiplier."""
    try:
        db = float(os.environ.get("ZOE_VOICE_GAIN", "4"))
    except ValueError:
        db = 4.0
    return 10.0 ** (db / 20.0)

def _apply_gain(pcm_bytes, factor):
    if factor == 1.0:
        return pcm_bytes
    import numpy as np
    a = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float32) * factor
    np.clip(a, -32768, 32767, out=a)
    return a.astype("<i2").tobytes()

def _stream_request(text, key, voice_id, output_format):
    body = json.dumps({"text": text, "model_id": MODEL,
                       "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}}).encode()
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
           f"?output_format={output_format}")
    req = urllib.request.Request(url, data=body,
        headers={"xi-api-key": key, "Content-Type": "application/json",
                 "Accept": "audio/mpeg", "User-Agent": "curl/8.19.0"})
    return urllib.request.urlopen(req, timeout=60)

def stream_pcm(text, key, voice_id, stop):
    """Stream pcm_24000 from ElevenLabs into sounddevice, chunk by chunk.

    Raises on any error so the caller can fall back to the blocking MP3 path.
    `stop` is a threading.Event; setting it aborts playback for barge-in.
    """
    import sounddevice as sd
    factor = _gain_factor()
    resp = _stream_request(text, key, voice_id, "pcm_24000")
    out = sd.RawOutputStream(samplerate=PCM_SR, channels=1, dtype="int16")
    out.start()
    leftover = b""
    try:
        while not stop.is_set():
            chunk = resp.read(4096)
            if not chunk:
                break
            data = leftover + chunk
            n = len(data) - (len(data) % 2)   # whole 16-bit frames only
            frame, leftover = data[:n], data[n:]
            if frame:
                out.write(_apply_gain(frame, factor))
    finally:
        try: resp.close()
        except Exception: pass
        try:
            out.abort() if stop.is_set() else out.stop()
            out.close()
        except Exception: pass

# Non-blocking speak with barge-in. A new call cancels the current utterance.
_worker = None
_stop = threading.Event()

def speak(text, key, voice_id):
    """Speak without blocking the caller. Cancels any utterance still playing."""
    global _worker, _stop
    stop_current()
    _stop = threading.Event()
    stop = _stop
    def run():
        try:
            stream_pcm(text, key, voice_id, stop)
        except Exception as e:
            if stop.is_set():
                return                      # barge-in, not a real failure
            try:                            # fall back to the known-good blocking path
                play(tts(text, key, voice_id))
            except Exception as e2:
                print("  (speak error:", e2, "| stream:", e, ")")
    _worker = threading.Thread(target=run, daemon=True)
    _worker.start()

def stop_current():
    """Cut off whatever is playing (barge-in / shutdown)."""
    global _worker
    try: _stop.set()
    except Exception: pass
    w = _worker
    if w and w.is_alive():
        w.join(timeout=2)

def wait_speech(timeout=None):
    """Block until the current utterance finishes (keeps the mic off her own voice)."""
    w = _worker
    if w:
        w.join(timeout)

def play(mp3_bytes):
    """Play mp3 with no popup: convert to wav via the bundled ffmpeg (loudness-maximized), winsound.

    Zoe is normalized to the ceiling so she is clearly audible. speechnorm pushes the speech up,
    a limiter keeps it from clipping. ZOE_VOICE_GAIN adds (or removes) dB on top -- default +4;
    raise it if you want her even louder, set it negative to back off. Falls back to a plain
    convert if this ffmpeg build lacks the filters, so playback never breaks.
    """
    import imageio_ffmpeg, winsound
    tmp = tempfile.mkdtemp(prefix="jarvis_voice_")
    mp3, wav = os.path.join(tmp, "v.mp3"), os.path.join(tmp, "v.wav")
    with open(mp3, "wb") as f:
        f.write(mp3_bytes)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        gain = float(os.environ.get("ZOE_VOICE_GAIN", "4"))
    except ValueError:
        gain = 4.0
    af = "speechnorm=e=25:r=0.0005:l=1,volume=%.1fdB,alimiter=limit=0.98" % gain
    try:
        subprocess.run([ff, "-y", "-i", mp3, "-af", af, wav], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
    except Exception:
        subprocess.run([ff, "-y", "-i", mp3, wav], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)   # fallback: original loudness
    winsound.PlaySound(wav, winsound.SND_FILENAME)  # synchronous, no window
    for p in (mp3, wav):
        try: os.remove(p)
        except OSError: pass

def main():
    load_env()
    key = os.environ.get("ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVENLABS_VOICE_ID")
    if not key or not voice:
        sys.exit("set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in .env")
    text = " ".join(sys.argv[1:]).strip() or sys.stdin.read().strip()
    if not text:
        sys.exit("nothing to say (pass text as an argument or on stdin)")
    try:
        audio = tts(text, key, voice)
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs error {e.code}: {e.read().decode('utf-8','replace')[:200]}")
    if audio[:1] == b"{":  # JSON error, not audio
        sys.exit("ElevenLabs returned an error: " + audio.decode("utf-8", "replace")[:200])
    play(audio)
    print(f"spoke {len(text)} chars in voice {voice}")

if __name__ == "__main__":
    main()
