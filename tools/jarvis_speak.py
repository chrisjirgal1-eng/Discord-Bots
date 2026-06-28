#!/usr/bin/env python3
"""JARVIS talk-back: turn text into speech in JARVIS's voice and play it.

Reads ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID from .env, calls ElevenLabs TTS,
and plays the audio. Voice-agnostic: whatever ELEVENLABS_VOICE_ID is set to is what
she speaks in, so it auto-uses the upgrade pick once the account is on Creator tier.

Usage:
  python tools/jarvis_speak.py "Wide awake, sir. What shall we build today?"
  echo "text" | python tools/jarvis_speak.py        # reads stdin if no arg
"""
import os, sys, json, tempfile, subprocess, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "eleven_turbo_v2_5"  # fast, low-latency, free-tier friendly

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
