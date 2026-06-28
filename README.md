# Discord-Bots

Chris's working repo. Three things live here, tied together:

1. A production **Discord music bot** (Python, discord.py).
2. A persistent **memory bank** so Claude remembers across sessions.
3. **JARVIS**, a personal AI OS layer built on Claude Code: one entry point that routes to skills,
   subagents, and connectors. See [JARVIS.md](JARVIS.md).

## The Discord music bot

A persistent, auto-joining music bot with slash commands.

- `bot.py`: the client, slash commands, voice lifecycle, per-guild locking and reconnection.
- `audio.py`: track fetching with yt-dlp, ffmpeg options.
- `queue_manager.py`: per-guild queues.
- `utils.py`: shared helpers (voice preconditions, duration formatting).
- `tests/`: 76 tests (`python -m pytest -q`).

Run it:

```sh
pip install -r requirements.txt
cp .env.example .env        # then add your DISCORD_TOKEN
python bot.py
```

Tests:

```sh
pip install -r requirements-test.txt
python -m pytest -q
```

## JARVIS (the AI OS layer)

Open Claude Code in this repo and say `jarvis, <request>`. The router reads the request, sends it
to the right skill, subagent, connector, or automation, and ends with the recommended next move.

- Entry point: `.claude/skills/jarvis/SKILL.md`. Wiring map and status: [JARVIS.md](JARVIS.md).
- Skills (`.claude/skills/`): jarvis, content-pipeline, caption, clearcoat-post, coach-email,
  zen-announce, digest-transcripts, memory-update, handoff. All content skills are draft only.
- Always-loaded rules (`.claude/rules/`): verification, model-routing, learning, coding-discipline,
  throughput.

What is wired and what still needs Chris's keys or a host is tracked honestly in JARVIS.md.

- Command center UI: `zoe-ui/index.html`, a live Iron Man-style telemetry HUD (arc reactor, gauges,
  graphs of real CPU, RAM, disk, and network from `tools/zoe_server.py` via psutil). Double-click
  `zoe.bat` to start the server and open it at localhost:7717. Standalone it shows a simulated feed.
- Zoe the assistant: `tools/zoe_assistant.py` (run `zoe.bat`) is wake-word driven. Say "Hey Zoe"
  then a request and she opens it in your browser (news, a YouTube search, a Google search, a site)
  and confirms out loud. Pipeline: mic voice-activity to Deepgram to Groq intent to browser plus
  ElevenLabs speech. `tools/jarvis_voice.py` is a simpler push-to-talk chat loop; `tools/jarvis_speak.py`
  just speaks text. The older card-style dashboard is `jarvis-ui/index.html`. Both HUDs have a theme
  switcher and a CONFIG block at the top. Tune `RMS_THRESHOLD` in zoe_assistant.py if the mic is too hot or too quiet.

## The memory bank

The model starts fresh each session; the committed files are the memory. `CLAUDE.md` auto-loads the
must-haves at the start of every session, the rest is read on demand.

- `memory-bank/`: instructions, identity, preferences, active-context, progress-log, projects,
  lessons, tools, autonomous-potential. `memory-bank/README.md` explains the ritual.
- `memory-bank/handoff.md`: the runbook a resumed session follows to continue work in progress.
- Update ritual: the `memory-update` skill, or say "jarvis, update memory". Commit and push, or it is lost.

## Tooling

- `tools/watch_batch.py`: downloads a list of video URLs and transcribes them with Groq Whisper
  (Windows-friendly, no PATH dependencies). Output lands in `transcripts/`.
- `transcripts/TECHNIQUES.md`: a ranked digest of techniques learned from saved videos.
- graphify: a code knowledge graph (`graphify-out/graph.json` is committed for ~0-token queries).
  Setup and commands in `memory-bank/tools.md`.
- 154 VoltAgent subagents, callable through the JARVIS router by task and model tier.

## Clearcoat Co. site

`clearcoatco-website/` is the booking site for Chris's detailing business (static, Vercel via
`vercel.json`, with a Google Apps Script backend). Open security findings are tracked in
`clearcoatco-website/SECURITY-NOTES.md`.

## Layout

```
bot.py, audio.py, queue_manager.py, utils.py   the music bot
tests/                                          76 tests
.claude/skills/                                 JARVIS skills (incl. the jarvis router)
.claude/rules/                                  always-loaded discipline rules
memory-bank/                                    durable cross-session memory
tools/                                          watch_batch + setup scripts
transcripts/                                    video transcripts + TECHNIQUES.md
clearcoatco-website/                            the Clearcoat booking site
CLAUDE.md, JARVIS.md                            session bootstrap + the AI OS map
```
