# JARVIS voice spec (the "wide awake, sir" loop)

The runbook to give JARVIS voice. Written so that once Chris adds two keys, wiring it is one
short session. Not built yet, because it needs his 11 Labs and Deepgram keys and a smoke test on
real hardware. This is the design and the exact steps, not a tested module.

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
ELEVENLABS_API_KEY=...                 # from elevenlabs.io, account settings (the one thing still needed)
ELEVENLABS_VOICE_ID=L1QogKoobNwLy4IaMsyA   # already chosen by Chris and preset in .env
DEEPGRAM_API_KEY=...                   # from deepgram.com console (only needed for listening)
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
