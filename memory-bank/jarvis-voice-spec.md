# JARVIS voice spec (the "wide awake, sir" loop)

The runbook for JARVIS voice. BUILT and live as of 2026-06-28: `tools/jarvis_speak.py` (talk-back
only) and `tools/jarvis_voice.py` (the full two-way loop). Keys are in `.env`. This doc is the
design behind them; the sections below describe the architecture they implement.

## Architecture

Reuse the whole existing setup instead of rebuilding the brain. The voice loop is just ears and
a mouth around the JARVIS router that already exists.

```
mic ──> Deepgram (speech to text) ──> `claude -p "jarvis, <text>"` ──> reply text ──> 11 Labs (text to speech) ──> speaker
```

The key move: route the transcribed text through the Claude Code CLI in headless print mode
(`claude -p`). That reuses every skill, rule, and MCP connector this repo already has, including
the `jarvis` router and its "synthesize the next move" rule. The voice layer adds nothing to the
brain; it only carries sound in and out.

## What Chris provides

In the gitignored `.env` (never commit these):

```
ELEVENLABS_API_KEY=...                 # set: talk-back is live via tools/jarvis_speak.py
ELEVENLABS_VOICE_ID=pFZP5JQG7iQjIQuC4Bku   # Lily (free tier, active). Upgrade pick: L1QogKoobNwLy4IaMsyA
DEEPGRAM_API_KEY=...                   # still needed for listening (the full two-way loop)
```

## Dependencies

```
pip install sounddevice websockets requests
```

`sounddevice` captures the mic and plays audio. `websockets` streams to Deepgram. `requests`
calls 11 Labs. The Claude Code CLI is already installed (`claude --version`).

## Reference flow (illustrative, verify on real hardware)

1. Capture mic audio with `sounddevice`, stream raw PCM to Deepgram's streaming endpoint over a
   websocket, read back the final transcript string.
2. Call the brain: `subprocess.run(["claude", "-p", f"jarvis, {transcript}"], capture_output=True, text=True)`.
   Use `--output-format text`. The stdout is the reply.
3. Speak it: POST the reply to `https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}`
   with the `xi-api-key` header, get back MP3 bytes, play them with `sounddevice` (decode via
   `imageio_ffmpeg`, already installed, or `pydub`).
4. Loop. Add a wake word or a push-to-talk key so it is not always listening.

## Activation steps

1. Add the three keys to `.env`.
2. `pip install sounddevice websockets requests`.
3. Build `jarvis_voice.py` from the flow above (or ask: "jarvis, build the voice loop from
   memory-bank/jarvis-voice-spec.md").
4. Smoke test: speak one command, confirm the round trip (heard, routed, spoken). Tune latency
   (use Deepgram streaming and 11 Labs `eleven_turbo` for speed).

## Guardrails carried in

The voice loop inherits every JARVIS guardrail because it routes through `claude -p`: it drafts
outward-facing actions instead of sending them, and it stops for Chris on anything credentialed or
irreversible. Voice does not loosen those; it just changes the input and output channel.
