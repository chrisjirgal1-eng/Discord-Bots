# JARVIS kickoff

Run this on Chris's home computer with Claude Code (where Instagram is reachable).
Open Claude Code in the Discord-Bots folder and say: "follow JARVIS-KICKOFF.md".

Goal: learn from the 65 saved videos, anchor on the 3 goal videos, apply the real
techniques, and connect everything into JARVIS, Chris's personal AI OS.

Work autonomously through the phases. Follow the rules in `.claude/rules/` the whole way:
verification (route quality judgment to a fresh subagent), learning (read memory-bank/lessons.md
first, append a lesson after a mistake), coding-discipline, throughput, model-routing.
Branch off the default branch for each change, scan for em dashes and the banned words
delve/leverage/fantastic before every commit, commit and push each step. Chris has until July 5.

## Phase 0: setup

- `git pull` to get the latest.
- Ensure deps: `pip install yt-dlp imageio-ffmpeg` (or confirm yt-dlp + ffmpeg are on PATH).
- Confirm `GROQ_API_KEY` is set in the environment (Chris's own, never printed or committed).
- Run the SessionStart hook setup if needed: graphify, the VoltAgent subagents, the watch plugin.

## Phase 1: transcribe (mechanical)

- Run `tools/watch-batch.sh tools/video-urls.txt transcripts/`.
- It downloads each video's audio with yt-dlp and transcribes with Groq Whisper.
- Image /p/ carousel posts have no audio and will be marked failed. That is expected.
- Commit `transcripts/` and push.

## Phase 2: digest, goals first

- Run the `/digest-transcripts` skill.
- Read the 3 GOAL transcripts FIRST as the north star: DZlQ7GZnJR7, DZu4FFeDtIH, DZVEN4gMRXV.
  They define what "the true Claude" and JARVIS should be. Capture that target in 3 to 5 lines.
- Then read the 62 training transcripts. Fan out Haiku subagents per chunk (model-routing).
- Write `transcripts/TECHNIQUES.md`: every video ranked technique | source | value | status
  (new / already-have / hype) | action. Judge each training technique against the goal: it earns
  a place only if it moves the setup toward what the goal videos describe.

## Phase 3: apply the real techniques

- For each NEW, high-value technique: implement the concrete change (a skill, a rule, a workflow,
  a connector, an automation). Keep it simple. No speculative abstractions.
- Verify each with a fresh subagent before shipping. Social videos overhype; apply only what survives.
- Commit each applied change on its own branch, then merge. Append lessons as you learn.
- Skip and log the hype and the already-have items. Quality over volume.

## Phase 4: build toward JARVIS and connect it

The 3 goal videos define the target. The training techniques are the means. Now assemble.

- Read `memory-bank/projects.md` for the JARVIS roadmap: voice I/O, Discord integration,
  Roblox/game automation, content pipeline, fitness/training tracking, Clearcoat Co. automation,
  unified dashboard.
- Map each goal-video capability and each applied technique to a JARVIS piece.
- Connect the pieces that already exist into a coherent whole: the skills (coach-email, caption,
  zen-announce, clearcoat-post, memory-update, digest-transcripts), the rules, graphify, the 154
  subagents, the MCP connectors (GitHub, Supabase, Vercel, Gmail, Slack, Notion, Calendar, Drive,
  Stripe, Zapier), and any new techniques from the videos.
- Build the missing connective pieces toward a single entry point: one place Chris talks to JARVIS
  and it routes to the right skill, agent, or automation. Start with what runs locally and is safe.
- Durable scheduling (nightly jobs, watchers) must run on a persistent host or GitHub Actions /
  Supabase / Zapier, not a session that ends. See memory-bank/autonomous-potential.md.

## Guardrails

- Reversible and internal: build, commit, merge freely.
- Irreversible or outward-facing (real emails, public posts, prod data, credentialed or security
  config): stop and flag for Chris first.
- Do not store raw passwords or secrets in the repo. Connectors use OAuth; API keys go in a
  gitignored env file.
- Do not overbuild. Every piece must trace to a goal-video target or a real Chris need.

## Done looks like

- transcripts/TECHNIQUES.md exists, ranked and honest.
- The genuinely useful techniques are applied and merged.
- The pieces are connected toward one JARVIS entry point, with a short map of what is wired and
  what still needs a persistent host or Chris's approval.
- memory-bank/active-context.md and progress-log.md updated. Lessons appended.
