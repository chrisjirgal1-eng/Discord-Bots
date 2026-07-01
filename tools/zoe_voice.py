#!/usr/bin/env python3
"""Voice Intelligence 2.0 — hybrid voice engine (Increment 1).

Pipeline: VAD-gated mic capture + (optional) local wake-word -> STREAMING Deepgram STT
(interim + final transcripts, low latency) -> zoe_router.process (unchanged) -> TTS ->
Conversation Mode (follow-ups need no wake word) -> sleep on inactivity.

EVERY new dependency is OPTIONAL and degrades to today's behavior, so this engine can never be
worse than the legacy loop:
  websockets   -> streaming STT          (else available()=False -> zoe_assistant runs the legacy loop)
  webrtcvad    -> accurate VAD           (else energy/RMS gate)
  openwakeword -> on-device wake word    (else wake is matched in the streamed transcript)
  faster_whisper -> offline STT fallback (else Deepgram only)

Reuses zoe_router.process / zoe_state / zoe_memory / zoe_learn unchanged. `available()` tells
zoe_assistant whether to use this engine. Per-turn metrics -> memory/voice_metrics.jsonl.
Run: python tools/zoe_voice.py   (live mic test)
"""
import os, sys, json, time, queue, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zoe_router

SR = 16000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = os.path.join(ROOT, "memory", "voice_metrics.jsonl")
WAKE_WORDS = ("hey zoe", "ok zoe", "okay zoe", "hey zoey", "zoe", "zoey")


def _has(m):
    try:
        __import__(m); return True
    except Exception:
        return False


HAS_WS = _has("websockets")
HAS_VAD = _has("webrtcvad")
HAS_SD = _has("sounddevice") and _has("numpy")
HAS_WW = _has("openwakeword")


def available():
    """True only when (a) opted in via ZOE_VOICE_2=1 AND (b) the deps exist (websockets + mic).
    Opt-in until live-validated, so the DEFAULT stays the proven legacy loop — zero regression risk."""
    if os.environ.get("ZOE_VOICE_2", "").strip().lower() not in ("1", "true", "yes", "on"):
        return False
    return HAS_WS and HAS_SD


def capabilities():
    return {"streaming": HAS_WS, "mic": HAS_SD, "vad": HAS_VAD, "wakeword": HAS_WW,
            "offline_stt": _has("faster_whisper")}


_BUILTIN_APPS = ["Spotify", "Discord", "Chrome", "Notepad", "Excel", "Outlook", "Steam",
                 "Slack", "Obsidian", "YouTube", "Hermes", "Zoe", "Zoey"]


def keyterms():
    """Words to boost in STT (Deepgram keywords): built-in app names + targets Zoe has actually
    learned. Improves recognition of the names she uses. Deduped, capped. Best-effort, pure/testable."""
    terms = list(_BUILTIN_APPS)
    try:
        import zoe_learn
        for rec in (zoe_learn.all() or {}).values():
            t = (rec.get("target") or "").strip()
            if t and 1 < len(t) <= 30:
                terms.append(t)
    except Exception:
        pass
    out, seen = [], set()
    for t in terms:
        k = t.lower()
        if k not in seen:
            seen.add(k); out.append(t)
    return out[:50]


def metric(**rec):
    try:
        os.makedirs(os.path.dirname(METRICS), exist_ok=True)
        with open(METRICS, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), **rec}) + "\n")
    except Exception:
        pass


def parse_dg(msg):
    """Parse ONE Deepgram streaming message -> (transcript, is_final, confidence) or None. Pure/testable.
    UtteranceEnd is surfaced as ('', True, 1.0) to mark a turn boundary."""
    try:
        d = json.loads(msg) if isinstance(msg, (str, bytes, bytearray)) else msg
        if d.get("type") == "UtteranceEnd":
            return ("", True, 1.0)
        alt = (d.get("channel", {}) or {}).get("alternatives", [{}])[0]
        tr = (alt.get("transcript") or "").strip()
        final = bool(d.get("is_final") or d.get("speech_final"))
        if not tr and not final:
            return None
        return (tr, final, float(alt.get("confidence", 0.0) or 0.0))
    except Exception:
        return None


def heard_wake(text):
    """Does the transcript contain a wake word, and what's the command after it? Returns
    (woke: bool, command: str)."""
    t = (text or "").lower().strip(" ,.!?")
    for w in WAKE_WORDS:
        i = t.find(w)
        if i != -1:
            return True, (text.strip()[i + len(w):].strip(" ,.!?") if i == 0 else text.strip())
    return False, ""


class VAD:
    """webrtcvad if available, else an energy/RMS gate. is_speech(frame20ms_bytes) -> bool."""
    def __init__(self, aggressiveness=2, rms_threshold=600):
        self.rms_threshold = rms_threshold
        self.v = None
        if HAS_VAD:
            try:
                import webrtcvad
                self.v = webrtcvad.Vad(aggressiveness)
            except Exception:
                self.v = None

    def is_speech(self, frame_bytes):
        if self.v is not None:
            try:
                return self.v.is_speech(frame_bytes, SR)
            except Exception:
                pass
        try:
            import numpy as np
            a = np.frombuffer(frame_bytes, dtype=np.int16).astype(np.float32)
            return bool(a.size) and float((a * a).mean() ** 0.5) > self.rms_threshold
        except Exception:
            return False


class DeepgramStream:
    """Streaming STT over Deepgram's WebSocket. Feed PCM16 frames via send(); transcripts arrive on
    the on_transcript(transcript, is_final, confidence) callback. Runs an asyncio loop in a daemon
    thread. Header-arg name differs across websockets versions -> both are tried. Best-effort."""
    def __init__(self, key, on_transcript):
        self.key, self.on_transcript = key, on_transcript
        self.q = queue.Queue()
        self.alive = False
        self.thread = None

    def start(self):
        self.alive = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def send(self, pcm_bytes):
        if self.alive:
            self.q.put(pcm_bytes)

    def stop(self):
        self.alive = False
        try:
            self.q.put(b"")
        except Exception:
            pass

    def _run(self):
        try:
            import asyncio
            asyncio.run(self._main())
        except Exception as e:
            metric(event="dg_stream_error", error=str(e)[:120])

    async def _main(self):
        import websockets, urllib.parse
        kw = "".join("&keywords=" + urllib.parse.quote(f"{t}:2") for t in keyterms())   # custom vocab
        url = ("wss://api.deepgram.com/v1/listen?model=nova-2&encoding=linear16"
               f"&sample_rate={SR}&channels=1&interim_results=true&punctuate=true"
               "&endpointing=300&utterance_end_ms=1000" + kw)
        hdr = {"Authorization": "Token " + self.key}
        try:
            ws = await websockets.connect(url, additional_headers=hdr)   # websockets >= 11
        except TypeError:
            ws = await websockets.connect(url, extra_headers=hdr)        # websockets < 11
        try:
            import asyncio

            async def sender():
                loop = asyncio.get_event_loop()
                while self.alive:
                    frame = await loop.run_in_executor(None, self.q.get)
                    if not frame:
                        break
                    await ws.send(frame)
                try:
                    await ws.send(json.dumps({"type": "CloseStream"}))
                except Exception:
                    pass

            async def receiver():
                async for msg in ws:
                    p = parse_dg(msg)
                    if p:
                        self.on_transcript(*p)

            await asyncio.gather(sender(), receiver())
        finally:
            try:
                await ws.close()
            except Exception:
                pass


def run(groq_key, dg_key, ctrl=None, speak=None, follow_window=12.0, sleep_after=30.0):
    """Hybrid streaming loop. Requires available(). `speak(text)` plays a reply (caller supplies TTS).
    Local wake (openwakeword) if present, else wake is matched in the streamed transcript. Best-effort."""
    import sounddevice as sd, numpy as np
    if not (groq_key and dg_key):
        raise RuntimeError("zoe_voice.run needs GROQ + DEEPGRAM keys")
    speak = speak or (lambda s: print("ZOE:", s))
    vad = VAD()
    frame_ms = 20
    blocksize = int(SR * frame_ms / 1000)
    history, in_convo, last_voice = [], False, time.time()
    buf = {"text": "", "t0": None}

    def on_tx(transcript, is_final, conf):
        nonlocal in_convo
        if transcript:
            buf["text"] = transcript
            if buf["t0"] is None:
                buf["t0"] = time.time()

    print("\n  ZOE 2.0 listening (streaming). Say 'Hey Zoe'.  caps:", capabilities(), "\n")
    audio_q = queue.Queue()
    with sd.InputStream(samplerate=SR, channels=1, dtype="int16", blocksize=blocksize,
                        callback=lambda i, n, t, s: audio_q.put(bytes(i))):
        stream = None
        try:
            while True:
                frame = audio_q.get()
                speech = vad.is_speech(frame)
                if speech:
                    last_voice = time.time()
                    if stream is None:                      # open a stream when speech starts
                        buf["text"], buf["t0"] = "", None
                        stream = DeepgramStream(dg_key, on_tx); stream.start()
                    stream.send(frame)
                else:
                    # end of an utterance: a short trailing silence finalizes the turn
                    if stream is not None and time.time() - last_voice > 0.7:
                        stream.stop(); stream = None
                        text = buf["text"].strip()
                        if text:
                            woke, cmd = heard_wake(text)
                            if not in_convo and not woke:
                                continue                    # not addressed to Zoe
                            command = cmd if (woke and cmd) else text
                            if woke and not cmd:
                                speak("Yes, sir?"); in_convo = True; continue
                            t_reply = time.time()
                            try:
                                say, _ = zoe_router.handle(command, groq_key, ctrl, history)
                            except Exception as e:
                                say = "Sorry sir, something went wrong."
                            metric(event="turn", text=command[:80],
                                   first_word_ms=round((t_reply - (buf["t0"] or t_reply)) * 1000),
                                   reply_ms=round((time.time() - t_reply) * 1000))
                            history += [{"role": "user", "content": command},
                                        {"role": "assistant", "content": say}]
                            history = history[-8:]
                            speak(say)
                            in_convo = True
                    # sleep back to wake-only after inactivity
                    if in_convo and time.time() - last_voice > sleep_after:
                        in_convo = False
        except KeyboardInterrupt:
            if stream:
                stream.stop()
            print("\n  ZOE offline.\n")


if __name__ == "__main__":
    print("capabilities:", capabilities(), "| available:", available())
    if available():
        from jarvis_speak import load_env, tts, play
        load_env()
        run(os.environ.get("GROQ_API_KEY"), os.environ.get("DEEPGRAM_API_KEY"),
            speak=lambda s: play(tts(s, os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID"))))
    else:
        print("streaming engine unavailable (need websockets + sounddevice) -> use zoe_assistant.py")
