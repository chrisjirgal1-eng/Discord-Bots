# Active Context

What is in flight right now. Updated each session. This is the first thing to trust.

## Latest: Zenthra dev team task dashboard LIVE (2026-07-27, PR #45 MERGED)

THE SITE IS LIVE. PRIMARY URL (2026-07-27, Chris did not want his name in the address):
- Member board: https://zenthra-dev-team.vercel.app/
- Admin board: https://zenthra-dev-team.vercel.app/admin.html
Vercel project zenthra-dev-team (Zen Peak Studios), created by Chris importing the
repo in the Vercel dashboard (Root Directory team-dashboard, framework Other); it
auto-redeploys on every push to the default branch. All 4 assets verified 200.
BACKUP URL still live on GitHub Pages (Actions workflow, also auto-redeploys):
https://chrisjirgal1-eng.github.io/Discord-Bots/ . PR #45 squash-merged (0f4f2d3).

Hosting saga (why not Vercel/Supabase): Vercel connector token cannot create projects
(403 on team AND personal scope, even after Chris approved); Supabase rewrites text/html
to text/plain on its domain. GitHub Pages needed two Chris steps: Settings > Pages >
Source = GitHub Actions, and the deploy had to run from the DEFAULT branch (the
github-pages environment rejects other branches, 1-second no-runner failures).

PINGS ARE LIVE (2026-07-27): Chris provided the webhook URL + his Discord user ID in
chat; both seeded into app_config. test_ping through the deployed admin function
returned ping_sent true. Every task completion now pings him with the proof image.
Admin passcode is seeded and was delivered in chat 2026-07-27. NOTHING is pending on
this build; next real step is Chris adding his first member and tasks on the admin board.

LOGIN CHANGE (2026-07-27, Chris's explicit choice): members log in with their Discord
USERNAME ONLY, no access codes. He accepted the tradeoff (anyone with the link + a
username can open that member's board); ownership checks and the mandatory proof
picture still hold server-side. ZEN-BBJ8-CCQ7 stays his ADMIN passcode, unchanged.
regen_code action and the code modal removed. 12/12 post-change API tests green,
including a real completion ping to his channel.

## Original build notes (2026-07-27, superseded status lines above)

Chris asked for a website to manage his dev team: members by Discord username, timezones,
weekly schedules, tasks he assigns, check-off that REQUIRES a proof screenshot, live progress,
and a Discord ping to him on every completion. Built, deployed, 35/35 e2e tests green.

- Backend LIVE: new free Supabase project `zenthra-team-dashboard` (rmbcnthetpiubiyasipp).
  Tables members/tasks/app_config (RLS deny-all), public `proofs` bucket, Edge Functions
  `admin` (passcode header) + `member` (username + access code). All auth is sha256 server-side;
  browser only ships the anon key. Decisions Chris made: access codes for member login,
  whole-team progress visible to everyone (members complete only their own tasks).
- Frontend: `team-dashboard/` static no-build (index.html member board, admin.html Chris board,
  shared.js, style.css). Proof upload compresses client-side to <=1600px JPEG; server caps 4MB;
  completion is atomic (no proof, no done). Ping failure never blocks completion; admin sees a
  "ping failed" badge + resend. Polling 10s/30s, live per-member local clocks via Intl.
- HOSTING PENDING (the one open piece): Vercel MCP deploy is approval-gated and the gate cannot
  reach Chris from a non-interactive session (tried twice, once after his explicit yes via
  AskUserQuestion). Supabase itself cannot render HTML (text/plain rewrite; site/sitepush
  functions are inert 410 stubs from that discovery). Fix is 2 minutes: interactive session
  "deploy team-dashboard to Vercel" + approve, or `npx vercel --prod` in team-dashboard/ on his
  PC. Boards also work opened as local files (API allows any origin).
- NEEDS CHRIS (then it is fully live): (1) approve the Vercel deploy, (2) Discord webhook URL
  from his chosen channel, (3) his Discord user ID. Seed SQL is in team-dashboard/README.md.
  Admin passcode is already seeded (delivered to him in chat 2026-07-27, changeable any time).
- e2e testing ran IN-DATABASE (Postgres http extension calling the live functions) because the
  sandbox egress policy blocks the new supabase.co domain. Test data cleaned; advisors clean
  (only intentional deny-all INFOs). NOTE: a weekly keep-alive Routine could NOT be armed (the
  scheduling MCP tools are approval-gated here). Free tier pauses after ~1 week idle; normal use
  keeps it awake, README documents restore_project, and a Routine can be armed from an
  interactive session later.
- PR #45 draft on branch claude/dev-team-task-dashboard-sj62bw, session subscribed and watching.

## Latest: yt-dlp cookies MERGED, Chris turned it on (2026-07-22, PR #42 merged to default)

Verified the YouTube code (tests + selftests + diagnostics all green). The cloud 403 was an egress
policy block, not a bug. Chris's real blocker was auth: YouTube bot-check + Instagram login. Built one
cookies convention every yt-dlp path reads. PR #42 MERGED to default. Chris exported his cookies.

- New `tools/ytdlp_cookies.py`: resolves YTDLP_COOKIES -> COOKIES -> `secrets/cookies.txt` (must exist).
- Wired into `audio.py` (Discord bot), `tools/watch_batch.py` (transcribe/research), `tools/zoe_music.py`.
- `.gitignore` blocks `secrets/` + `cookies.txt` (a live login must never be committed). Verified: no
  cookies file ever tracked; only the code files (ytdlp_cookies.py, its test, COOKIES-SETUP.md) are in git.
- `COOKIES-SETUP.md`: export steps (Get cookies.txt LOCALLY) for YouTube + Instagram, where to put it.
- 27 tests pass. PR #42 merged 2026-07-22 (self-assigned, then merged on Chris's go under standing authority).
- Chris did the export. Target runtime is his LOCAL PC (Zoey/JARVIS, open network), NOT cloud. Delivery:
  code via git (pull default), cookies stay local (secrets/cookies.txt or YTDLP_COOKIES, never committed).
- NEXT FOR CHRIS: on his PC, `git pull` default, confirm `python tools/ytdlp_cookies.py` prints the path.
- OPEN: his "plugins/commands/skills auto" ask is vague; scope pending.

## Latest: ZOE loop kill switch (2026-07-01, PR #40, branch claude/zoey-loop-control-g2x6b8)

Chris had Zoey running Claude Code 24/7, which held a file lock on the Claude desktop app
("Another program is currently using this file"), so he couldn't open Claude Code himself.
There was no voice way to stop it: "go to sleep" only naps the session, and with
ZOE_REALTIME_GATE=always it reopens. Built a voice off switch. NOT yet merged (PR #40 draft).

- New tool `stop_loop` (tools/zoe_tools.py + tools/zoe_ops.py). Say "turn off the loop",
  "let go of Claude Code", or "I want to open Claude Code" and she frees the app but keeps
  listening. Scope Chris chose: kill Claude Code only, Zoey stays alive.
- Kill is PRECISE, not a bare "claude" substring: the app by name (Claude.exe) + the CLI by
  entrypoint (claude-code, \claude.exe/.cmd, \claude\...cli, a bare "claude " command). A
  .claude config path or a claude.ai browser tab do NOT match; browsers + Code.exe skipped.
- Zoey's own process tree (self + verified ancestors, with a PID-reuse guard) is protected.
- Passed as base64 -EncodedCommand so the match can't hit its own command. Emits one JSON line.
- Respawn honesty: killing a child can't stop a scheduled task / wrapper that relaunches it, so
  it does NOT claim to. It SCANS read-only for a scheduled task whose action runs Claude Code and
  returns it as `respawn`; she offers to disable it on his yes (confirm-first, no silent config).
- Elevation gap surfaced: a matched-but-unkillable process comes back as `nokill` and ok=False,
  so she never says "free to open" when it may still be locked.
- Reviewed by a fresh Opus code-reviewer; its findings (over-broad match, respawn over-promise,
  elevation gap, PID reuse, stdout/stderr parse) all fixed in a second commit. Selftests pass, 23 tools.
- OPEN: Chris is not sure what launches the 24/7 run. If it's a scheduled task, stop_loop detects
  and offers to disable it. If it's a plain .bat/.vbs loop not named "claude", detection can't see
  it yet -- get the launch mechanism from him and extend it so the off switch is durable.

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
