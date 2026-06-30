# Active Context

What is in flight right now. Updated each session. This is the first thing to trust.

## Latest: self-evolving system + live UI (2026-06-30, PR #39, branch claude/zoe-evolve, draft)

Built Zoey's permanent self-improvement layer, easiest-first, all four phases shipped to one draft PR.
NOT merged. Needs Chris to test, add one secret, and run the videos locally.

- Phase 1 (free, immediate): security agent on GitHub Actions (zoe-security.yml) running gitleaks +
  pip-audit + npm audit + bandit + semgrep. CI ran green; found one real CVE (PyNaCl 1.5.0 ->
  CVE-2025-69277, fix 1.6.2). Plus the 69 new IG reels appended to tools/video-urls.txt and a
  creator registry at memory-bank/creators.md.
- Phase 2: the evolving loop (zoe-evolve.yml). Daily + manual. Runs Claude headless to make ONE
  verified improvement, opens a DRAFT PR, never pushes to default. Token-efficient (Sonnet driver,
  escalates only when needed). Gated on the ANTHROPIC_API_KEY repo secret -- a no-op until Chris adds it.
- Phase 3: the agents/ framework. Each agent = a folder with an AGENT.md charter + a blackboard
  section. Security is live; content/research/ops are scaffolds (charters only, routed to existing
  skills, turned on later by enabling a workflow). Shared state in agents/blackboard.md (no DB).
- Phase 4: the live UI. zoe_server.py gained /agents + /workflow endpoints (read agents/*, skills,
  findings, blackboard). zoe-ui/index.html now shows real skill names, per-agent status pills, a
  WORKFLOW panel with a green/amber/red security badge, and real chip counts. The faked 132/10 are gone.
- Rejected as too heavy (kept it lean): CrewAI, LangGraph, Postgres, Supabase, Mem0, n8n. Blackboard
  is a committed file; agents are skill/subagent prompts + Actions runners; memory stays file-based.
- Also this session: watch_batch.py OpenAI Whisper fallback + watch.bat one-click; cookie exports
  gitignored (live session tokens).
- Needs Chris: add ANTHROPIC_API_KEY secret (arms the loop); run the 69 videos locally then
  /digest-transcripts (Instagram is proxy-walled in the cloud); smoke-test the UI on Windows.
  GitHub MCP needs re-auth before a session can open/update PRs.

## Earlier: ZOE speech-to-speech voice system (2026-06-30, PR #37, branch claude/voice-realtime)

Built ZOE's realtime voice: she talks like the demo videos, runs in the Electron desktop app, and
can act on the machine. NOT yet merged (PR #37 is draft); test, then merge to default.

- Stack: OpenAI Realtime API (gpt-realtime, voice "marin") is her ears+brain+mouth in one
  speech-to-speech model. Her powers are wired in as function tools through the existing zoe_router.
- New files: `tools/zoe_realtime.py` (the agent + wake gate), `tools/zoe_tools.py` (22 tools),
  `tools/zoe_browser.py` (Playwright browser she operates), `tools/zoe_music.py` (background music),
  `tools/zoe_ops.py` (read_file + run_command). Launchers: `zoe_silent.vbs`, `zoe_stop.bat`.
- Electron app (`electron/main.js`) now spawns zoe_realtime.py as its voice (was zoe_assistant.py).
  Launch = the desktop app (UI) + realtime voice in one. `npm install` then `npm start`, or
  double-click `zoe_silent.vbs`.
- Wake word "Hey Zoe" is transcribed by OpenAI Whisper (NO Deepgram, his Deepgram key was dead;
  her OpenAI key carries it). Idle is free (local RMS gate, ZOE_MIC_THRESHOLD=500); only the wake
  utterance + the live session cost money. ZOE_REALTIME_GATE=always for hands-free always-on.
- The 22 tools: launch/close apps, open folders, open_web, search_platform (YT/TikTok/IG/X/Twitch/
  Spotify/Reddit/Roblox), search_site (any site), open_in_account (Chrome profiles, no passwords
  stored), browser_open/read/click/type/back/forward/scroll, play/stop/set_music, recall_memory,
  run_agent (Hermes, needs Hermes installed), read_file, run_command, start_workspace.
- Safety posture Chris chose: confirm-before-irreversible. browser_click/type and run_command refuse
  destructive actions (buy/pay/delete/post/send/rm/format/force-push) unless confirmed=true.
- Reviewed by fresh code-reviewers at each stage; findings fixed. Cloud can't test audio, so Chris
  smoke-tests on Windows. Confirmed working: app + voice + "Hey Zoe" + English + detailed replies.
- Still to test: music (needs a track in `music/`), web browsing, the read_file/run_command fixing.

## Earlier: JARVIS kickoff run (2026-06-27, local Windows machine)

Ran JARVIS-KICKOFF.md end to end on Chris's own PC (the persistent runtime host). All merged
to the default branch and pushed.

- 65 videos transcribed (57 reels + 8 image-post captions). See transcripts/ and TECHNIQUES.md.
- Cookie note: Instagram needs login; Chrome/Edge app-bound encryption blocks yt-dlp. The
  working path is a cookies.txt export from the browser (Get cookies.txt LOCALLY extension).
  Do not store the cookie file in the repo. See lessons.md.
- Merged the 4 Devin branches (tests, error handling, shared utils, security). 53/53 tests pass.
- Applied one new technique: the handoff skill. Skipped the hype, logged why in TECHNIQUES.md.
- Built the JARVIS entry point: /jarvis router skill + root JARVIS.md map. One door that routes
  and recommends the next move.
- Autonomous follow-on (Chris away, blanket authority): made the setup live on this machine.
  graphify installed (pip graphifyy 0.8.50) and graph rebuilt (400 nodes, 545 edges). The 154
  VoltAgents installed via the canonical marketplace (10 bundles, user scope), register next session.
  Built the content-pipeline skill (scout, topic, hook, script, routes to caption), draft only,
  verified, merged. Wired into the jarvis router.
- Still needs Chris (credentialed, left untouched): voice keys (11 Labs + Deepgram) and a 24/7
  host (GitHub Actions / Zapier). Auto-posting stays gated. Those are the next builds.
- Cross-session autobuild armed: scheduled task `jarvis-autobuild` (daily ~9am) reads
  `memory-bank/handoff.md` and does one verified backlog item per run. Runs while the Claude app is
  open (or next launch), not a cloud daemon. Manage or stop it from the Scheduled sidebar.
- The whole safe backlog was already done live this session (not left for the daily runs): security
  audit (clearcoatco-website/SECURITY-NOTES.md), tests for utils + watch_batch (76 green), root
  README, voice spec + inert CI template, VoltAgents coverage audit. handoff.md is now BACKLOG
  DRAINED. The autobuild will confirm and park until Chris provides the credentialed items.
- What is left needs Chris (credentialed): voice keys (11 Labs + Deepgram), a 24/7 host + secrets
  (or just rename the CI template to turn on tests), auto-post approval, and the Clearcoat site fixes.

## Current focus (2026-06-27)

- Set up this persistent memory bank so Claude remembers across sessions. DONE this session.
- Added token-efficiency playbook and terse output rules. DONE.
- Installed graphify (code knowledge graph). Built semantic graph of this repo:
  83 nodes, 119 edges, 10 communities. Committed graph.json so future sessions query
  for ~0 tokens. See memory-bank/tools.md. DONE.
- Added SessionStart hook (.claude/hooks/session-start.sh, async) so every web session
  auto-installs graphify and loads the setup. Functionally permanent. DONE.
- Documented claude-mem and openclaw: both work on a local machine/VPS, not cloud. DONE.
- All of the above merged to the default branch (PRs #5 and #6). The setup is now LIVE:
  the hook runs automatically on every future web session. DONE.

## Overnight autonomous run (2026-06-27, merged on its own)

Standing directive: keep building and merging cloud-safe work until Chris says stop.
Shipped and merged this run:
- PR #13 autonomous-potential plan (memory-bank/autonomous-potential.md, ARIS-blueprinted).
- PR #14 verification rule, #19 learning rule, plus model-routing rule. All always-loaded now.
- PR #15/#16 Discord bot: review + all concurrency/leak/DM fixes (verified, needs a dev-guild smoke test).
- PR #17/#18 four draft-only skills: coach-email, caption, zen-announce, clearcoat-post.
- PR #19 learning loop: memory-bank/lessons.md anti-repetition memory + .claude/rules/learning.md.
- PR #20 portable installer: tools/install-claude-setup.sh (global or per-repo) so any project
  or plain Claude Code gets this whole setup. See tools/PORTABLE-SETUP.md.

Active discipline rules (read them): verification.md (writer never grades its own work),
learning.md (read lessons.md before similar work, append after a mistake), model-routing.md.

## Autonomous roadmap (read this first when back, 2026-06-27 overnight)

- Full plan: `memory-bank/autonomous-potential.md`. Built from the ARIS harness via a
  6-agent research workflow, adversarially verified.
- First move (highest value): fix the KOS 409 deploy. Needs a session scoped to the KOS
  repo, which this session cannot reach.
- Cloud-safe autonomous builds I am working through overnight: commit a chosen ARIS skill
  subset so it persists, audit the 154 VoltAgents, then the roadmap NEXT items.
- Key limit confirmed: no schedule fires on its own after a web session ends. Durable
  scheduling must run on GitHub Actions, Supabase, or Zapier (all free).
- Standing directive: keep working autonomously, commit each result, until Chris says stop.

## Standing authority (granted 2026-06-27)

- Chris granted blanket permission to do build/dev work without asking: write code,
  run commands, commit, push, open AND merge PRs, install dev tooling, and choose the
  best options to evolve and improve the coding setup.
- Guardrails kept by judgment, not permission: do not delete work I did not create,
  do not send outward-facing messages to other people, and flag credentialed or
  irreversible security config before doing it.

## Recently established

- All major MCP connectors are live: GitHub, Supabase, Vercel, Gmail, Drive, Calendar,
  Notion, Slack, Stripe, Zapier, Figma, Asana, Linear, Atlassian, Windsor.ai.
- Discord runs through Zapier, not a native connector.
- Twitter/X and TikTok direct posting are blocked at the platform level.
- This GitHub session is scoped to the chrisjirgal1-eng/discord-bots repo only.

## Open threads to pick back up

- KOS deploy: 409 empty repository error on the GitHub Actions workflow.
  Likely the INDEX_REPOS variable or a workflow edit not fully propagating.
  Needs the separate KOS repo, which this session cannot reach.
- JARVIS: Python files partially assembled, not fully delivered. Windows/OneDrive target.

## Working branch

- claude/vibrant-cray-tui7og (the default; origin/HEAD). Branch fresh off it for each change.
