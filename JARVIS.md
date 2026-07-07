# JARVIS

Chris's personal AI OS. One command center he owns, not rented. Built on Claude Code:
the skills, rules, memory bank, knowledge graph, subagents, and MCP connectors already in
this repo, tied together behind a single entry point.

This is the map: what each goal capability is, which piece implements it, and whether it
runs today, needs a host, or needs Chris's keys. The 3 goal videos define the target. The
training videos were the means. This is the assembly.

## Talk to it

Say `jarvis, <request>` or run `/jarvis`. It reads the request, routes to the right skill,
subagent, connector, or automation, and ends with the recommended next move. The router is
`.claude/skills/jarvis/SKILL.md`. The rule it never breaks: synthesize to the next move,
never just display.

## Capability map

| Goal capability | Piece that implements it | Status |
|---|---|---|
| Persistent memory, no re-reading from scratch | `memory-bank/` + graphify graph (`graphify-out/graph.json`) | wired, local |
| Knowledge graph of how things connect | graphify (tree-sitter graph, ~70x fewer tokens/search) | wired, local |
| One entry point that routes | `jarvis` skill (this build) | wired, local |
| Judgment that points to the next move | synthesis rule baked into the `jarvis` skill | wired, local |
| Specialist workers | 154 VoltAgent subagents + model-routing | wired, local |
| Drafting: coach email, captions, guild news, Clearcoat | `coach-email`, `caption`, `zen-announce`, `clearcoat-post` skills | wired, drafts only |
| Learn from saved videos | `digest-transcripts` skill + `tools/watch_batch.py` | wired, local |
| Session continuity, no context rot | `handoff` skill + `memory-update` skill | wired, local |
| Reach into real services | MCP: GitHub, Supabase, Vercel, Gmail, Drive, Calendar, Notion, Slack, Stripe, Zapier | wired, credentialed |
| Loops that act, verify, report | verification.md discipline (verifier not the writer, budget cap) | rule wired, runtime needs a host |
| Voice in and out ("Wide awake, sir") | 11 Labs TTS + Deepgram STT (cascade), or OpenAI Realtime speech-to-speech (`tools/zoe_realtime.py`) | needs Chris's keys |
| Content pipeline of named agents | `content-pipeline` orchestrates discrete stage skills `scout`, `topic`, `hook`, `script`, then routes to `caption` | wired, draft only |
| Always-on, 24/7 | GitHub Actions / Supabase / Zapier (a web session cannot stay alive) | needs a host |

## What runs locally today

This machine is the JARVIS runtime host. Right now, with no extra setup:

- `/jarvis <request>` routes across every skill, subagent, and connector above.
- The memory bank and graphify give it persistent context for near zero tokens.
- It drafts outward-facing work (emails, posts) and stops for Chris to send, by guardrail.
- It runs the video pipeline end to end: `tools/watch_batch.py` then `digest-transcripts`.

## What needs Chris before it is real

Honest about the gap, so nothing is wired blind:

1. **Voice.** Two modes, both keyed in the gitignored `.env`, never the repo.
   - **Cascade** (cheap, ~$0.02/min): 11 Labs TTS + Deepgram STT. The loop is mic to Deepgram
     to JARVIS router to 11 Labs to speaker. Runbook: `memory-bank/jarvis-voice-spec.md`.
   - **Realtime** (demo-grade, metered): OpenAI Realtime is her ears, brain, and mouth in one
     speech-to-speech model, with all her powers wired in as tools. Needs `OPENAI_API_KEY`.
     `python tools/zoe_realtime.py`. She idles in a free local wake-listen and only opens the
     paid session while you talk, then closes it on silence so cost stays bounded.
2. **24/7 loops.** A web session cannot fire a schedule after it ends. The nightly and
   watcher jobs run on GitHub Actions (free) or Zapier. Each writes a heartbeat so a missed
   run is visible. See `memory-bank/autonomous-potential.md`.
3. **Auto-posting.** The content pipeline is built and wired as the `content-pipeline` skill
   (scout, topic, hook, script, then routes to caption), draft only. It produces a review-ready
   package; Chris records and posts. The only piece left needing his sign-off is letting it
   post on its own, which is outward-facing and stays gated by guardrail. Roadmap detail:
   `memory-bank/autonomous-potential.md` items H and K.

## Architecture in one read

```
Chris ──"jarvis, ..."──> /jarvis router ──┬─> skills (coach-email, caption, zen-announce,
                                          │            clearcoat-post, digest, memory, handoff)
   reads context from                     ├─> 154 VoltAgent subagents (right model tier)
   memory-bank + graphify  <──────────────┤
                                          ├─> MCP connectors (GitHub, Gmail, Slack, ...)
                                          └─> automations (Actions / Zapier, once hosted)
                          every response ends with the recommended next move
```

The pieces already existed. JARVIS is the wiring and the one door.
