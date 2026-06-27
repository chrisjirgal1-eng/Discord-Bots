# Active Context

What is in flight right now. Updated each session. This is the first thing to trust.

## Current focus (2026-06-27)

- Set up this persistent memory bank so Claude remembers across sessions. DONE this session.
- Added token-efficiency playbook and terse output rules. DONE.
- Installed graphify (code knowledge graph). Built semantic graph of this repo:
  83 nodes, 119 edges, 10 communities. Committed graph.json so future sessions query
  for ~0 tokens. See memory-bank/tools.md. DONE.
- Added SessionStart hook (.claude/hooks/session-start.sh) so every web session
  auto-installs graphify and loads the setup. Functionally permanent. DONE.
- Documented claude-mem: works on local machine, not cloud sessions. DONE.

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
