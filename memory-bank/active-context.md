# Active Context

What is in flight right now. Updated each session. This is the first thing to trust.

## Latest: JARVIS kickoff run (2026-06-27, local Windows machine)

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
