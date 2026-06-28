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

1. [x] DONE 2026-06-27. Security + quality audit. Bot/Python clean (already verified in the Devin
   merge, 53 tests pass). Website had real findings, flagged not auto-changed (they alter the live
   deployed site, Chris's call): see clearcoatco-website/SECURITY-NOTES.md (public log_job write +
   client-side admin password; reviews auto-publish; stats computed over unfiltered rows; GET writes;
   raw error leakage). A fresh reviewer verified the findings and caught a missed stat-poisoning
   issue, which was added. No source behavior changed.
2. [x] DONE 2026-06-27. Added tests/test_utils.py (23 tests: format_duration, is_script_url_configured,
   require_playing_or_paused, require_voice_client, ensure_voice_connection connect/move/idle paths)
   and tests/test_watch_batch.py (vid_id parsing). Suite now 76 green. A fresh reviewer claimed the
   async tests were vacuous (missing the asyncio marker); verified empirically with a planted failing
   assertion, which DID fail, proving asyncio_mode=auto runs them. Reviewer was wrong; tests are real.
3. [x] DONE 2026-06-27. Added root README.md (the bot, JARVIS, the memory bank, tooling, the
   Clearcoat site, a layout map). Verified every referenced path exists and the 76-test claim is
   accurate (Type-A self-check). The banned-word scan caught em dashes in the first draft; all fixed.
4. [x] DONE 2026-06-27. Wrote memory-bank/jarvis-voice-spec.md (the voice loop: mic to Deepgram to
   `claude -p "jarvis, ..."` to 11 Labs to speaker, the keys, deps, activation steps) and an inert
   CI template `.github/workflows/jarvis-ci.yml.disabled` (runs the 76 tests; the .disabled suffix
   keeps GitHub from firing it; rename to enable). YAML validated. Cross-linked the voice spec in
   JARVIS.md. No secrets, nothing auto-fires.
5. [x] DONE 2026-06-27. All 10 VoltAgent bundles loaded and registered (164 agent files: core-dev 12,
   lang 31, infra 17, qa-sec 18, data-ai 14, dev-exp 16, domains 15, biz 17, meta 12, research 12).
   Noted coverage and the high-value agents for Chris in tools.md, plus the correction that the
   canonical marketplace-add works locally (only the cloud session needs the tarball workaround).
6. [ ] When 1-5 are done or all remaining are BLOCKED: write "BACKLOG DRAINED, waiting on Chris"
   below, list exactly what Chris must provide (voice keys, host secrets, auto-post approval), stop.

## Tried and failed (do not repeat)

- yt-dlp cannot read Chrome/Edge app-bound cookies; external COM decrypt is refused. Use a browser
  cookie-export extension (cookies.txt) or Firefox. Cookie file stays out of the repo.
- Native Windows Python cannot open Git Bash `/c/...` paths; use `C:/...` or the Read tool.

## Next step

BACKLOG DRAINED, waiting on Chris. Items 1 to 5 are done and pushed. Do not invent more work or
refactor working code. A resumed session should confirm this, then stop.

What Chris must provide to go further (all credentialed, none doable autonomously):
- Voice: an 11 Labs API key + a chosen voice ID, and a Deepgram API key, in `.env`. Then say
  "jarvis, build the voice loop from memory-bank/jarvis-voice-spec.md".
- 24/7 automation: turn the CI on (rename `.github/workflows/jarvis-ci.yml.disabled` to `.yml`),
  and for nightly jobs, add the needed secrets to the repo and a host (GitHub Actions / Zapier).
- Auto-posting: explicit approval before the content-pipeline is allowed to post rather than draft.
- The deployed Clearcoat site fixes in `clearcoatco-website/SECURITY-NOTES.md` are his call to apply
  and redeploy.

If Chris adds any of the above, that becomes the next item. Until then, there is nothing safe left
to build without him.
