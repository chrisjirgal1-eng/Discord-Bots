#!/usr/bin/env python3
"""JARVIS two-way voice loop: she hears you, thinks, and answers out loud.

Pipeline: microphone -> Deepgram (speech to text) -> Groq llama (the JARVIS brain)
-> ElevenLabs (text to speech) -> speakers. All keys read from .env.

Usage:
  python tools/jarvis_voice.py
  Press Enter, speak, press Enter again. She replies in her voice. Ctrl+C to quit.

This is the conversational loop. For routing to the actual skills, agents, and MCP
connectors, talk to JARVIS in Claude Code instead; this is the fast spoken layer.
"""
import os, sys, io, wave, json, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_speak import load_env, tts, play  # reuse the talk-back engine

SR = 16000
GROQ_MODEL = "llama-3.3-70b-versatile"
ZOE = (
    "You are Zoe, Chris's personal AI assistant: a warm, witty, confident AI like the one from "
    "Iron Man, but your name is Zoe. Address him as 'sir' or 'Chris'. You know his world: "
    "Zenthra (his Roblox guild), Clearcoat Co. (his detailing business), his content, his coding, "
    "and D1 track goals. This is spoken aloud, so keep replies SHORT and natural: one to three "
    "sentences, no markdown, no lists, no emoji, no stage directions. Be capable and a little playful."
)

def record():
    import sounddevice as sd, numpy as np
    frames = []
    stream = sd.InputStream(samplerate=SR, channels=1, dtype="int16",
                            callback=lambda indata, n, t, s: frames.append(indata.copy()))
    input("  press Enter, then speak: ")
    stream.start()
    input("  listening... press Enter when done: ")
    stream.stop(); stream.close()
    if not frames:
        return None
    return np.concatenate(frames, axis=0)

def to_wav(audio):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(audio.tobytes())
    return buf.getvalue()

def stt(wav_bytes, key):
    req = urllib.request.Request(
        "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&punctuate=true",
        data=wav_bytes, headers={"Authorization": f"Token {key}", "Content-Type": "audio/wav"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return d["results"]["channels"][0]["alternatives"][0]["transcript"].strip()

def brain(text, history, key):
    msgs = [{"role": "system", "content": ZOE}] + history + [{"role": "user", "content": text}]
    body = json.dumps({"model": GROQ_MODEL, "messages": msgs, "max_tokens": 160, "temperature": 0.7}).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "curl/8.19.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"].strip()

def main():
    load_env()
    groq = os.environ.get("GROQ_API_KEY")
    dg = os.environ.get("DEEPGRAM_API_KEY")
    el = os.environ.get("ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVENLABS_VOICE_ID")
    missing = [n for n, v in [("GROQ_API_KEY", groq), ("DEEPGRAM_API_KEY", dg),
                              ("ELEVENLABS_API_KEY", el), ("ELEVENLABS_VOICE_ID", voice)] if not v]
    if missing:
        sys.exit("missing in .env: " + ", ".join(missing))

    print("\n  ZOE voice loop. Press Enter to talk, Ctrl+C to quit.\n")
    history = []
    try:
        while True:
            audio = record()
            if audio is None or len(audio) < SR * 0.3:
                print("  (didn't catch that)\n"); continue
            try:
                text = stt(to_wav(audio), dg)
            except Exception as e:
                print("  stt error:", e, "\n"); continue
            if not text:
                print("  (silence)\n"); continue
            print("  you:    ", text)
            try:
                reply = brain(text, history, groq)
            except Exception as e:
                print("  brain error:", e, "\n"); continue
            print("  ZOE:    ", reply, "\n")
            history += [{"role": "user", "content": text}, {"role": "assistant", "content": reply}]
            history = history[-8:]
            try:
                play(tts(reply, el, voice))
            except Exception as e:
                print("  speak error:", e, "\n")
    except KeyboardInterrupt:
        print("\n  Goodbye, sir.\n")

if __name__ == "__main__":
    main()
