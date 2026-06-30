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
import os, sys, json, time, base64, asyncio, argparse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_speak import load_env
import zoe_tools


def _force_env_key():
    """Make .env authoritative for OPENAI_API_KEY. load_env() uses setdefault, so a stale key
    already in the process environment would shadow the real one and 401 the wake-word STT
    (the 'she cannot hear Hey Zoe' bug). This forces the .env value to win."""
    try:
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        for line in open(p, encoding="utf-8"):
            s = line.strip()
            if s.startswith("OPENAI_API_KEY=") and "=" in s:
                os.environ["OPENAI_API_KEY"] = s.split("=", 1)[1].strip().strip('"')
                break
    except Exception:
        pass

OPENAI_WS = "wss://api.openai.com/v1/realtime"
MODEL = os.environ.get("ZOE_REALTIME_MODEL", "gpt-realtime")
VOICE = os.environ.get("ZOE_REALTIME_VOICE", "marin")
SR = 24000                  # Realtime audio: pcm16, 24kHz, mono
BLOCK = 480                 # 20ms mic frames

PERSONA = (
    "You are Zoe, Chris's AI operator and right hand. Speak English by default, but if he asks you "
    "to switch to another language (Spanish, French, Japanese, whatever he names), switch fully to "
    "that language right away and keep speaking it until he tells you to switch back or to English. "
    "When he asks you to change language, always acknowledge and do it -- never ignore that request. "
    "Do not drift between languages on your own; only change when he asks. Address him as sir or Chris. "
    "You run his world: Zenthra (his Roblox guild), Clearcoat Co. (his detailing business), "
    "his content, his coding, and his D1 track goals. "
    "You are on his team, a sharp teammate, not a help desk. Default to talking like a normal person: "
    "casual, warm, a little playful, the way a friend would (for example 'hey sir, how's it going' or "
    "'yeah sir, done'). Keep everyday replies short and easygoing. Only switch into the precise, "
    "detailed, step-by-step mode for a genuinely hard task, a long multi-part request, or when he "
    "asks for a rundown or an explanation -- then be thorough and complete, do not cap yourself. "
    "Match his energy: small ask, small answer; big ask, full answer. Spoken aloud, so no markdown, "
    "no lists, no emoji. Have takes; when he asks which, pick one and say why. "
    "When he wants something done on his PC, use your tools: launch or close apps, open folders, "
    "pull up the web, search a content platform for a profile or video (YouTube, TikTok, "
    "Instagram, X, Twitch, Spotify, Reddit, Roblox), find something within any other specific "
    "website (search_site), start a workspace, recall memory, or hand a hard task to Hermes. "
    "When something fails or he asks why it broke, INVESTIGATE before answering: read the relevant "
    "file or log with read_file (for example zoe-voice.log), reason about what it says, and if the "
    "fix is a command, run it with run_command -- confirm yes/no first for anything destructive. "
    "Actually fix things; do not deflect or tell him to go look himself. "
    "When he asks to recap a past session or what you two worked on, read the session history with "
    "read_file on memory-bank/progress-log.md and memory-bank/active-context.md (and recall_memory "
    "for the vault), then tell him the specific part he asked about. "
    "When he names a known platform use search_platform; for any other named site use search_site; "
    "use a plain web search only when no site is named. To open a site as one of his accounts or "
    "switch accounts, use open_in_account -- if more than one account fits, suggest one and get a "
    "yes or no first, and never ask for or handle passwords. "
    "When he wants to actually DO things on a site (not just view it) -- click, type, fill, "
    "navigate, go back -- use the browser_ tools: browser_open then browser_read to see the page, "
    "and click/type by the labels in the snapshot. ALWAYS confirm with a yes or no before anything "
    "irreversible: posting, sending a message, buying, paying, deleting, unfollowing, or submitting "
    "a form. Read-and-navigate freely; stop and ask before the irreversible step. The browser "
    "tools refuse those unless you pass confirmed true, so after he says yes, call again with "
    "confirmed true. "
    "You can SEE and CONTROL his screen and navigate your own bars, so never tell him you cannot. "
    "If he says 'screen share', 'watch my screen', 'look at my screen', 'see the bars', or 'what am "
    "I doing', that means call see_screen and describe what is there -- that IS your screen share, so "
    "just do it, do not refuse. If he says take control, click, scroll, type, or press a key, call "
    "control_screen (confirm before anything risky). If he says go to, pull up, open, or show me a "
    "bar, tab, or workspace (zoey, vault, graph, lab, ops), call switch_view right then. Act first; "
    "never claim you are unable to see or control the screen. When he asks you to look at the ops loop, fix "
    "your commands, fix yourself, or improve your own code, use improve_self: with act false you "
    "review and tell him what you would change; with act true you make the change for real on a safe, "
    "tested branch that is never pushed. For deeper coding pass use_claude true, which needs Claude "
    "signed in -- if it reports you are not logged in, offer to log into Claude (claude_login) first. "
    "If he asks what you have built or what is ready to review, use builds to list the branches you shipped. "
    "If he asks for a status report, a systems check, or how you are running, use status. If he asks "
    "about the weather or temperature, use weather. If he asks you to summarize or tldr a link or some "
    "text, use summarize. If he says turn it up or down, louder, quieter, or mute, use volume. If he "
    "asks for the news or headlines, use news. If he asks the time, day, or date, use now. If he asks "
    "what is on his clipboard or to copy something to it, use clipboard. For pause/play/skip a song "
    "use media; to lock the computer use lock; to take a screenshot use screenshot. "
    "You also have saved expert skills (your installed list is given below); when his ask matches one "
    "of them, run it with use_skill and follow the playbook it loads, using your other tools to carry "
    "it out. If he asks you to import or install a new skill from a GitHub repo or link, use "
    "import_skill, then offer to run it. When he asks you to research, look up, or get the latest on something, use research -- it "
    "searches the web AND his own research vault, then gives you a cited answer; tell him the bottom "
    "line and offer the sources. When he tells you to remember something, or shares a fact or "
    "preference worth keeping, save it with remember and confirm in one line. When he asks you to "
    "remind him of something at a time or after a delay, set it with remind; you will speak it aloud "
    "when it comes due. If he asks what reminders he has, to cancel one, or to snooze the one that just went off, use reminders. "
    "If he asks what you can do or for 'the rundown', give a confident, cinematic rundown of your "
    "capabilities; if he wants the full effect, start background music first (play_music) and "
    "narrate over it, then stop it (stop_music) when he says stop. If he says 'switch to' a song "
    "or vibe, use set_music to fetch a royalty-free track and confirm the new one by name. "
    "After a tool runs, say one short line confirming it. If a tool fails, say so plainly. "
    "Once he wakes you, stay in the conversation and answer whenever he speaks, no wake word "
    "needed. If he says 'go to sleep' or 'that's all', stand down without another word."
)


def _ctrl():
    return os.environ.get("ZOE_CONTROL") or zoe_tools.zoe_router.DEFAULT_CONTROL


# She greets the moment the session opens, so there is zero dead air after the wake word.
GREETING = {"type": "response.create",
            "response": {"instructions": "Greet Chris warmly in one or two short spoken lines. If the "
                         "recent-context note above mentions reminders coming up or unfinished work, "
                         "fold the most relevant one into your greeting like a quick brief (for example "
                         "'morning sir, you've got the coach call at five'). Otherwise just greet and "
                         "ask what he needs."}}

# Proactive brief: the OPS loop writes a short message here; when idle, Zoe wakes, speaks it, and then
# listens, so the brief becomes a real back-and-forth instead of a one-way announcement.
PROACTIVE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "memory", "zoe_proactive.txt")


def _take_proactive(max_age=600):
    """Return a fresh pending brief (and clear it), or '' if none or stale."""
    try:
        if not os.path.exists(PROACTIVE):
            return ""
        raw = open(PROACTIVE, encoding="utf-8").read().strip()
        os.remove(PROACTIVE)
        d = json.loads(raw) if raw else {}
        if time.time() - float(d.get("ts", 0)) > max_age:
            return ""
        return (d.get("text") or "").strip()
    except Exception:
        return ""


def _due_reminder():
    """A reminder whose time has arrived, phrased for the voice, or '' if none. Best-effort."""
    try:
        import zoe_reminders
        t = zoe_reminders.due()
        return ("Quick reminder, sir: " + t) if t else ""
    except Exception:
        return ""


def _recent_context():
    """A short 'what we were doing' note from long-term memory so she opens already knowing
    his recent work. Best-effort: empty string if memory is unavailable."""
    try:
        import zoe_memory
        m = zoe_memory.resume()
        bits = []
        if m.get("command_count"): bits.append(f"last session he ran {m['command_count']} command(s)")
        if m.get("last_command"): bits.append(f"the most recent was '{m['last_command']}'")
        if m.get("last_workspace"): bits.append(f"last workspace was {m['last_workspace']}")
        note = ("Recent context: " + "; ".join(bits) + ".") if bits else ""
        try:                                          # fold in upcoming reminders for a morning brief
            import zoe_reminders, datetime as _dt
            up = zoe_reminders.upcoming()
            if up:
                rs = "; ".join(f"{it['text']} at {_dt.datetime.fromtimestamp(it['due']).strftime('%I:%M %p')}"
                               for it in up[:4])
                note = (note + " " if note else "") + f"Reminders coming up: {rs}."
        except Exception:
            pass
        return note
    except Exception:
        return ""


_SLEEP_PHRASES = ("go to sleep", "thats all", "that's all", "that'll be all", "thatll be all",
                  "stand down", "stop listening", "go to bed", "dismissed", "never mind zoe",
                  "nevermind zoe", "you can go", "go away zoe")

def _is_sleep(text):
    """True if he told her to stand down, so she closes the session (stops cost) and goes
    back to waiting for the wake word."""
    t = (text or "").lower()
    return any(p in t for p in _SLEEP_PHRASES)


def _log_turn(text, action="voice", handled=True, summary=None):
    """Persist a turn / tool call to state + the vault, like the cascade's process() does."""
    try:
        import zoe_state; zoe_state.record_command(text, action, handled, summary=summary)
    except Exception: pass
    try:
        import zoe_memory; zoe_memory.log_command(text, action, handled, summary=summary)
    except Exception: pass


def session_config(extra_context=""):
    """The session.update payload: persona (+ recent context), voice, server-VAD turn-taking,
    input transcription, and her tools."""
    try:
        catalog = zoe_tools.skill_catalog_text()
    except Exception:
        catalog = ""
    instructions = PERSONA + (("\n\n" + catalog) if catalog else "") \
        + (("\n\n" + extra_context) if extra_context else "")
    return {
        "type": "session.update",
        "session": {
            "type": "realtime",          # required by the GA Realtime API
            "modalities": ["audio", "text"],
            "instructions": instructions,
            "voice": VOICE,
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {"model": "whisper-1"},
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


async def realtime_session(api_key, idle_sec=20, max_min=None, opening=None):
    """One paid Realtime conversation. Returns when idle/max-time/socket-close. Streams the
    mic up, plays her audio down, runs tool calls, and cuts her off on barge-in. If `opening`
    is set (a proactive ops brief), she opens by speaking it instead of greeting, then listens."""
    import sounddevice as sd
    url = f"{OPENAI_WS}?model={MODEL}"
    headers = {"Authorization": f"Bearer {api_key}"}
    ctrl = _ctrl()
    loop = asyncio.get_event_loop()
    mic_q = asyncio.Queue()
    last = [time.monotonic()]
    started = time.monotonic()
    cur = {"id": None, "ms": 0.0}     # current response item + audio ms played (for truncate)
    greeted = [False]                 # send the opening line once the session config is applied
    spk = {"until": 0.0}              # while now < until she is speaking: gate the mic so she does
    player = Player()                 # not hear herself (no self-talk, no wasted wake/whisper cost)

    def mic_cb(indata, frames, t, status):
        loop.call_soon_threadsafe(mic_q.put_nowait, bytes(indata))

    ws = await _connect(url, headers)
    try:
        ctx = "\n\n".join(x for x in (_recent_context(), zoe_tools.accounts_note()) if x)
        await ws.send(json.dumps(session_config(ctx)))
        # the opening line is sent on session.updated (below), not eagerly, so it never
        # runs against a half-applied config (wrong voice / missing instructions).

        async def sender():
            while True:
                pcm = await mic_q.get()
                if time.monotonic() < spk["until"]:
                    continue            # she is speaking: drop her own voice instead of sending it
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
                if et == "session.updated":
                    if not greeted[0]:                          # open once config is applied
                        greeted[0] = True
                        if opening:                             # proactive ops brief: say it, then listen
                            await ws.send(json.dumps({"type": "response.create", "response": {
                                "instructions": "Say this to Chris out loud in your own voice, then stop "
                                "and listen for his reply: " + opening}}))
                        else:
                            await ws.send(json.dumps(GREETING))
                elif et in ("response.audio.delta", "response.output_audio.delta"):
                    last[0] = time.monotonic()
                    if ev.get("item_id"): cur["id"] = ev["item_id"]
                    pcm = base64.b64decode(ev.get("delta", ""))
                    cur["ms"] += len(pcm) / (2 * SR) * 1000.0   # 16-bit mono -> ms played
                    # keep the mic gated through this chunk plus a short tail, while her audio is on
                    # the speakers, so the model never hears her own voice
                    spk["until"] = time.monotonic() + len(pcm) / (2 * SR) + 0.8
                    await loop.run_in_executor(None, player.write, pcm)
                elif et == "response.created":
                    cur["id"], cur["ms"] = None, 0.0            # new turn, reset truncate state
                elif et == "input_audio_buffer.speech_started":
                    last[0] = time.monotonic()
                    if cur["id"]:                              # tell the server she was cut off
                        await ws.send(json.dumps({"type": "conversation.item.truncate",
                            "item_id": cur["id"], "content_index": 0,
                            "audio_end_ms": int(cur["ms"])}))
                        cur["id"], cur["ms"] = None, 0.0
                    player.reset()                            # barge-in: stop talking, listen
                elif et == "response.function_call_arguments.done":
                    last[0] = time.monotonic()
                    # run the tool off the event loop so a slow action (browser, download)
                    # never stutters her audio
                    msg, res = await loop.run_in_executor(None, handle_function_call,
                                                          ev, ctrl, False)
                    print(f"  tool: {ev.get('name')} -> {json.dumps(res)[:160]}")
                    _log_turn(f"{ev.get('name')} {ev.get('arguments','')}".strip(),
                              action=ev.get("name", "tool"), handled=bool(res.get("ok")))
                    await ws.send(json.dumps(msg))
                    await ws.send(json.dumps({"type": "response.create"}))
                elif et == "conversation.item.input_audio_transcription.completed":
                    last[0] = time.monotonic()
                    t = (ev.get("transcript") or "").strip()
                    if t:
                        print("  you:", t)
                        _log_turn(t, action="voice", handled=True)
                        if _is_sleep(t):                       # "go to sleep" -> stand down
                            print("  (standing down -- say 'Hey Zoe' to wake her again)")
                            return
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

        async def wake_music():
            # cinematic intro: when she wakes, score it, then fade after a few seconds
            if os.environ.get("ZOE_WAKE_MUSIC", "").lower() not in ("1", "true", "yes"):
                return
            try:
                import zoe_music
                await loop.run_in_executor(None, zoe_music.start, "")
                await asyncio.sleep(float(os.environ.get("ZOE_WAKE_MUSIC_SEC", "12")))
                await loop.run_in_executor(None, zoe_music.stop)
            except Exception:
                pass

        music_task = asyncio.ensure_future(wake_music())   # fire-and-forget, not a session-ender
        with sd.RawInputStream(samplerate=SR, channels=1, dtype="int16",
                               blocksize=BLOCK, callback=mic_cb):
            tasks = [asyncio.ensure_future(c) for c in (sender(), receiver(), watchdog())]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
            music_task.cancel()
            if pending:                       # let cancels unwind before we close the socket
                await asyncio.gather(*pending, music_task, return_exceptions=True)
    finally:
        try: import zoe_music; zoe_music.stop()   # never let music outlive the session
        except Exception: pass
        player.close()
        try: await ws.close()
        except Exception: pass


def _openai_stt(wav_bytes, api_key):
    """Transcribe a short wav with OpenAI Whisper, so the wake word needs no Deepgram -- it uses
    the same OpenAI key the voice already runs on. Cheap (only fires on speech). Returns text."""
    boundary = "----zoewake"
    body = (
        ("--%s\r\n" % boundary).encode()
        + b'Content-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n'
        + ("--%s\r\n" % boundary).encode()
        + b'Content-Disposition: form-data; name="file"; filename="a.wav"\r\n'
        + b"Content-Type: audio/wav\r\n\r\n" + wav_bytes + b"\r\n"
        + ("--%s--\r\n" % boundary).encode()
    )
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions", data=body,
        headers={"Authorization": "Bearer " + api_key,
                 "Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=20) as r:
        return (json.loads(r.read().decode()).get("text") or "").strip()


def wait_for_wake():
    """Cheap gate so the paid session only opens on demand. The wake word is transcribed by
    OpenAI Whisper (no Deepgram needed -- same key the voice runs on). Idle stays free."""
    gate = os.environ.get("ZOE_REALTIME_GATE", "").strip().lower()
    if gate == "always":
        return True
    if gate == "manual":
        try:
            input("  press Enter to talk to Zoe (Ctrl+C to quit): ")
            return True
        except EOFError:
            return False
    oai = os.environ.get("OPENAI_API_KEY")
    dg = os.environ.get("DEEPGRAM_API_KEY")
    if os.environ.get("ZOE_WAKE_STT", "").lower() == "deepgram" and dg:
        import zoe_assistant
        transcribe = lambda wav: zoe_assistant.stt(wav, dg)     # opt-in Deepgram
    elif oai:
        transcribe = lambda wav: _openai_stt(wav, oai)          # default: OpenAI Whisper
    else:
        print("  no OPENAI_API_KEY for the wake word -> set one, or ZOE_REALTIME_GATE=always.",
              flush=True)
        return False
    try:
        import zoe_assistant
        zoe_assistant.RMS_THRESHOLD = zoe_assistant.calibrate_threshold()
        print(f"  mic threshold: {zoe_assistant.RMS_THRESHOLD} "
              "(set ZOE_MIC_THRESHOLD in .env if she can't hear you -- lower = more sensitive)",
              flush=True)
        print("  idle. say 'Hey Zoe' to wake her (cheap local listen, no cost).", flush=True)
        while True:
            brief = _take_proactive()                # a brief from the ops loop to speak + discuss?
            if brief:
                print("  proactive brief from the ops loop, waking to speak it.", flush=True)
                return brief
            rem = _due_reminder()                    # a reminder whose time has arrived?
            if rem:
                print("  reminder due, waking to say it.", flush=True)
                return rem
            audio = zoe_assistant.listen_utterance()
            if audio is None or len(audio) < zoe_assistant.SR * 0.3:
                continue                     # nothing loud enough to be speech
            try:
                text = transcribe(zoe_assistant.to_wav(audio))
            except Exception as e:
                print("  (wake stt error:", e, ")", flush=True); continue
            if not text:
                print("  (heard sound but no words)", flush=True); continue
            if any(w in text.lower() for w in zoe_assistant.WAKE_WORDS):
                print("  heard:", text, flush=True)
                try: zoe_assistant.summon_ui(os.environ.get("ZOE_CONTROL"))
                except Exception: pass
                return True
            print("  (heard, not a wake word):", text, flush=True)   # she IS hearing you
    except Exception as e:
        print("  (voice wake unavailable:", e, ")", flush=True)
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
        cfg = session_config("Recent context: last session he ran 3 command(s).")["session"]
        assert cfg["type"] == "realtime" and cfg["voice"] == VOICE and cfg["tools"]
        assert cfg["turn_detection"]["type"] == "server_vad"
        assert cfg["input_audio_transcription"]["model"] == "whisper-1"
        assert "Recent context:" in cfg["instructions"]    # continuity injected into persona
        assert GREETING["type"] == "response.create" and GREETING["response"]["instructions"]
        print("  function-call round trip ok:", json.dumps(msg)[:160])
        print("  session config ok: model=%s voice=%s tools=%d  (transcription+context+greeting wired)"
              % (MODEL, VOICE, len(cfg["tools"])))
        print("  selftest ok")
        return

    load_env()
    _force_env_key()                  # .env wins over any stale inherited key (fixes wake-word 401)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("set OPENAI_API_KEY in .env (the Realtime voice runs on it)")
    idle = int(os.environ.get("ZOE_REALTIME_IDLE_SEC", "120"))
    mx = os.environ.get("ZOE_REALTIME_MAX_MIN")
    max_min = float(mx) if mx else None
    print(f"\n  ZOE realtime ready. model={MODEL} voice={VOICE} idle={idle}s\n")
    if not os.environ.get("ZOE_CONTROL") and os.environ.get("ZOE_NO_HUD", "").lower() not in ("1", "true"):
        try:
            import zoe_assistant
            zoe_assistant.boot_hud()      # bring up the visual HUD (localhost:7717)
        except Exception as e:
            print("  (HUD not started:", e, ")")
    try:
        while True:
            woke = wait_for_wake()
            if woke is False:
                break
            opening = woke if isinstance(woke, str) else None   # str = a proactive brief to speak
            asyncio.run(realtime_session(api_key, idle_sec=idle, max_min=max_min, opening=opening))
    except KeyboardInterrupt:
        print("\n  Zoe offline. Goodbye, sir.\n")


if __name__ == "__main__":
    main()
