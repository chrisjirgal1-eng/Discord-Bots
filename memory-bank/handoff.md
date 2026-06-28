# Handoff: autonomous JARVIS build (resume here)

This file is the runbook for a resumed session (scheduled or manual). Read it first, do the
NEXT undone item with full discipline, then update this file. Chris is away until July 5, 2026.
He authorized continuing the build across sessions. The model resets each run; this file carries.

## Goal

Evolve the JARVIS setup toward the goal-video target (Claude agentic OS: persistent graph
memory, autonomous loops, voice, synthesis to the next move) by doing only SAFE, INTERNAL,
VERIFIED work. Drain the backlog below, then park. Done condition: backlog empty or every
remaining item is blocked on Chris's credentials.

## Hard guardrails (no human is watching, so these are strict)

- Reversible and internal only: code, docs, tests, skills, local installs, commits.
- NEVER do outward-facing or credentialed work: no real emails, no public posts, no deploys to
  prod, no creating or guessing API keys, no spending money, no touching Chris's browser or his
  personal `.claude` settings. If an item needs any of those, mark it BLOCKED and move on.
- One item per run. Verify with a fresh subagent (verification.md) before committing. Run the
  test suite (`python -m pytest -q`, 53 tests) when code changes. Scan banned words/em dashes.
- Branch off the default (`claude/vibrant-cray-tui7og`) per item, merge, push. Commit each step.
- Budget per run: stop after one backlog item plus its verification. Do not loop further.
- Do NOT invent work or refactor working code for its own sake (coding-discipline.md). When the
  backlog is drained, write "BACKLOG DRAINED, waiting on Chris" here and STOP.

## State now (2026-06-27, pushed to default)

65 videos transcribed + TECHNIQUES.md. 4 Devin branches merged (53 tests pass). 9 skills incl.
jarvis + content-pipeline. graphify live (400-node graph). 154 VoltAgents installed. JARVIS.md
map honest about wired vs gated. Everything committed and pushed.

## Backlog (do the top undone item, mark it done with a date)

1. [ ] Security + quality audit of the product code: bot.py, audio.py, utils.py, queue_manager.py,
   and clearcoatco-website/ (google-apps-script.js handles untrusted input; index.html renders
   sheet data). Route to a fresh reviewer (voltagent-qa-sec:security-auditor or :code-reviewer).
   Apply ONLY high-confidence real fixes. Re-run pytest. Commit. If clean, record "audited, clean".
2. [ ] Extend tests to the new modules: utils.py (ensure_voice_connection no-voice path,
   format_duration, is_script_url_configured) and tools/watch_batch.py (vid_id parsing, load_env).
   Keep them fast and offline (no network, no Discord). Verify green. Commit.
3. [ ] Add a clean root README.md that makes the repo legible (what it is, the bot, JARVIS, how
   the memory bank works). Confirm every skill/file it references exists. Commit.
4. [ ] Write ready-to-run specs so the credentialed pieces are one step for Chris: a voice runbook
   (11 Labs + Deepgram wiring) and an INERT GitHub Actions template committed as a documented
   non-running file (e.g. `.github/workflows/jarvis-nightly.yml.disabled`) so it cannot auto-fire.
   These are docs/templates only. Do not enable anything that needs secrets.
5. [ ] Quick audit of the 154 VoltAgents: confirm the 10 bundles loaded, note coverage in tools.md.
6. [ ] When 1-5 are done or all remaining are BLOCKED: write "BACKLOG DRAINED, waiting on Chris"
   below, list exactly what Chris must provide (voice keys, host secrets, auto-post approval), stop.

## Tried and failed (do not repeat)

- yt-dlp cannot read Chrome/Edge app-bound cookies; external COM decrypt is refused. Use a browser
  cookie-export extension (cookies.txt) or Firefox. Cookie file stays out of the repo.
- Native Windows Python cannot open Git Bash `/c/...` paths; use `C:/...` or the Read tool.

## Next step

Item 1 (security + quality audit). Branch: claude/vibrant-cray-tui7og.
