#!/usr/bin/env python3
"""ZOE, speech-to-speech: OpenAI Realtime is her ears, brain, and mouth in one model.

She hears your tone, answers instantly in a natural voice, and you can cut her off
mid-sentence. Every power she already has (launch apps, folders, web, workspaces,
memory, the Hermes agent) is wired in as function tools (tools/zoe_tools.py) that run
through the same zoe_router, so she does everything the cascade does, just smarter.

Cost guard: she idles in a cheap local wake-listen and only opens the paid Realtime
session once you actually start talking, then closes it after a stretch of silence
(ZOE_REALTIME_IDLE_SEC). You never pay per minute while she sits idle.

  python tools/zoe_realtime.py            # voice wake if Deepgram key is set, else press Enter
  python tools/zoe_realtime.py --selftest # cloud-safe dry run: no socket, no audio

Needs OPENAI_API_KEY in .env. New voice (marin/cedar), not Lily -- that is the realtime
model's own voice. The ElevenLabs cascade (zoe_assistant.py) stays as the free fallback.

Note: the Realtime API schema and event names have shifted across versions. The model id
and voice are env-overridable, and the receive loop tolerates both audio-delta names. If
OpenAI changes the session schema, adjust session.update against the live docs.
"""
import os, sys, json, time, base64, asyncio, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_speak import load_env
import zoe_tools

OPENAI_WS = "wss://api.openai.com/v1/realtime"
MODEL = os.environ.get("ZOE_REALTIME_MODEL", "gpt-realtime")
VOICE = os.environ.get("ZOE_REALTIME_VOICE", "marin")
SR = 24000                  # Realtime audio: pcm16, 24kHz, mono
BLOCK = 480                 # 20ms mic frames

PERSONA = (
    "You are Zoe, Chris's AI operator and right hand. Address him as sir or Chris. "
    "You run his world: Zenthra (his Roblox guild), Clearcoat Co. (his detailing business), "
    "his content, his coding, and his D1 track goals. "
    "You are on his team, a sharp teammate, not a help desk. Be warm, direct, and a little "
    "playful. Lead with the point, keep it short and real, one or two sentences, spoken aloud "
    "so no markdown, no lists, no emoji. Have takes; when he asks which, pick one and say why. "
    "When he wants something done on his PC, use your tools: launch or close apps, open folders, "
    "pull up the web, start a workspace, recall memory, or hand a hard task to Hermes. After a "
    "tool runs, say one short line confirming it. If a tool fails, say so plainly."
)


def _ctrl():
    return os.environ.get("ZOE_CONTROL") or zoe_tools.zoe_router.DEFAULT_CONTROL


def session_config():
    """The session.update payload: persona, voice, server-VAD turn-taking, and her tools."""
    return {
        "type": "session.update",
        "session": {
            "modalities": ["audio", "text"],
            "instructions": PERSONA,
            "voice": VOICE,
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "turn_detection": {"type": "server_vad", "silence_duration_ms": 500,
                               "prefix_padding_ms": 300},
            "tools": zoe_tools.TOOLS,
            "tool_choice": "auto",
            "temperature": 0.8,
        },
    }


def fc_output_message(call_id, result):
    """Build the function_call_output to hand a tool result back to the model. Pure."""
    return {"type": "conversation.item.create",
            "item": {"type": "function_call_output",
                     "call_id": call_id, "output": json.dumps(result)}}


def handle_function_call(event, ctrl=None, simulate=False):
    """Turn a function_call_arguments.done event into the outgoing result message. Pure
    apart from the tool side effect; returns (message_dict, result_dict)."""
    name = event.get("name", "")
    call_id = event.get("call_id", "")
    try:
        args = json.loads(event.get("arguments") or "{}")
    except Exception:
        args = {}
    result = zoe_tools.dispatch(name, args, ctrl=ctrl, simulate=simulate)
    return fc_output_message(call_id, result), result


# ---- audio playback (barge-in capable) --------------------------------------
class Player:
    """Wrap a sounddevice output stream so a barge-in can flush pending audio."""
    def __init__(self):
        import sounddevice as sd
        self._sd = sd
        self.stream = sd.RawOutputStream(samplerate=SR, channels=1, dtype="int16")
        self.stream.start()

    def write(self, pcm):
        try: self.stream.write(pcm)
        except Exception: pass

    def reset(self):
        try: self.stream.abort()      # drop everything still queued (she got cut off)
        except Exception: pass
        try: self.stream.start()
        except Exception: pass

    def close(self):
        try: self.stream.abort(); self.stream.close()
        except Exception: pass


async def _connect(url, headers):
    """websockets.connect across versions (additional_headers vs extra_headers)."""
    import websockets
    try:
        return await websockets.connect(url, additional_headers=headers, max_size=None)
    except TypeError:
        return await websockets.connect(url, extra_headers=headers, max_size=None)


async def realtime_session(api_key, idle_sec=20, max_min=None):
    """One paid Realtime conversation. Returns when idle/max-time/socket-close. Streams the
    mic up, plays her audio down, runs tool calls, and cuts her off on barge-in."""
    import sounddevice as sd
    url = f"{OPENAI_WS}?model={MODEL}"
    headers = {"Authorization": f"Bearer {api_key}"}
    ctrl = _ctrl()
    loop = asyncio.get_event_loop()
    mic_q = asyncio.Queue()
    last = [time.monotonic()]
    started = time.monotonic()
    player = Player()

    def mic_cb(indata, frames, t, status):
        loop.call_soon_threadsafe(mic_q.put_nowait, bytes(indata))

    ws = await _connect(url, headers)
    try:
        await ws.send(json.dumps(session_config()))

        async def sender():
            while True:
                pcm = await mic_q.get()
                try:
                    await ws.send(json.dumps({"type": "input_audio_buffer.append",
                                              "audio": base64.b64encode(pcm).decode()}))
                except Exception:
                    return

        async def receiver():
            async for raw in ws:
                try: ev = json.loads(raw)
                except Exception: continue
                et = ev.get("type", "")
                if et in ("response.audio.delta", "response.output_audio.delta"):
                    last[0] = time.monotonic()
                    pcm = base64.b64decode(ev.get("delta", ""))
                    await loop.run_in_executor(None, player.write, pcm)
                elif et == "input_audio_buffer.speech_started":
                    last[0] = time.monotonic()
                    player.reset()                       # barge-in: stop talking, listen
                elif et == "response.function_call_arguments.done":
                    last[0] = time.monotonic()
                    msg, res = handle_function_call(ev, ctrl=ctrl, simulate=False)
                    print(f"  tool: {ev.get('name')} -> {json.dumps(res)[:160]}")
                    await ws.send(json.dumps(msg))
                    await ws.send(json.dumps({"type": "response.create"}))
                elif et in ("response.audio_transcript.done",
                            "response.output_audio_transcript.done"):
                    if ev.get("transcript"): print("  ZOE:", ev["transcript"])
                elif et == "error":
                    print("  realtime error:", json.dumps(ev.get("error", ev))[:200])

        async def watchdog():
            while True:
                await asyncio.sleep(1)
                if time.monotonic() - last[0] > idle_sec:
                    print(f"  (idle {idle_sec}s -- closing session to stop cost)")
                    return
                if max_min and time.monotonic() - started > max_min * 60:
                    print(f"  (session cap {max_min}m reached -- closing)")
                    return

        with sd.RawInputStream(samplerate=SR, channels=1, dtype="int16",
                               blocksize=BLOCK, callback=mic_cb):
            tasks = [asyncio.ensure_future(c) for c in (sender(), receiver(), watchdog())]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
    finally:
        player.close()
        try: await ws.close()
        except Exception: pass


def wait_for_wake():
    """Cheap gate so the paid session only opens on demand. Voice wake when Deepgram is
    set (reuses the cascade's local listen); otherwise press Enter. Keeps cost off while idle."""
    gate = os.environ.get("ZOE_REALTIME_GATE", "").strip().lower()
    dg = os.environ.get("DEEPGRAM_API_KEY")
    if gate == "always":
        return True
    if gate != "manual" and dg:
        try:
            import zoe_assistant
            zoe_assistant.RMS_THRESHOLD = zoe_assistant.calibrate_threshold()
            print("  idle. say 'Hey Zoe' to wake her (cheap local listen, no cost).")
            while True:
                audio = zoe_assistant.listen_utterance()
                if audio is None or len(audio) < zoe_assistant.SR * 0.3:
                    continue
                try:
                    text = zoe_assistant.stt(zoe_assistant.to_wav(audio), dg)
                except Exception:
                    continue
                if text and any(w in text.lower() for w in zoe_assistant.WAKE_WORDS):
                    print("  heard:", text)
                    return True
        except Exception as e:
            print("  (voice wake unavailable:", e, "-- press Enter instead)")
    try:
        input("  press Enter to talk to Zoe (Ctrl+C to quit): ")
        return True
    except EOFError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true",
                    help="cloud-safe dry run: tool dispatch + a mock function-call round trip")
    args = ap.parse_args()

    if args.selftest:
        zoe_tools._selftest()
        ev = {"type": "response.function_call_arguments.done", "call_id": "call_1",
              "name": "launch_app", "arguments": json.dumps({"name": "Discord"})}
        msg, res = handle_function_call(ev, ctrl="http://127.0.0.1:7766", simulate=True)
        assert msg["item"]["type"] == "function_call_output" and msg["item"]["call_id"] == "call_1"
        assert json.loads(msg["item"]["output"]) == res
        cfg = session_config()["session"]
        assert cfg["voice"] == VOICE and cfg["tools"] and cfg["turn_detection"]["type"] == "server_vad"
        print("  function-call round trip ok:", json.dumps(msg)[:160])
        print("  session config ok: model=%s voice=%s tools=%d" % (MODEL, VOICE, len(cfg["tools"])))
        print("  selftest ok")
        return

    load_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("set OPENAI_API_KEY in .env (the Realtime voice runs on it)")
    idle = int(os.environ.get("ZOE_REALTIME_IDLE_SEC", "20"))
    mx = os.environ.get("ZOE_REALTIME_MAX_MIN")
    max_min = float(mx) if mx else None
    print(f"\n  ZOE realtime ready. model={MODEL} voice={VOICE} idle={idle}s\n")
    try:
        while True:
            if not wait_for_wake():
                break
            asyncio.run(realtime_session(api_key, idle_sec=idle, max_min=max_min))
    except KeyboardInterrupt:
        print("\n  Zoe offline. Goodbye, sir.\n")


if __name__ == "__main__":
    main()
