# Active Context

What is in flight right now. Updated each session. This is the first thing to trust.

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

- claude/kos-setup-rlf1c8
