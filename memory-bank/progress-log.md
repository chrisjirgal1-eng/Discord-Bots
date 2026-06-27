# Progress Log

Dated session history. Newest at the bottom. Format: YYYY-MM-DD.
Keep entries short. One idea per line.

## 2026-06-27

- Built the persistent memory bank in the discord-bots repo.
- Created root CLAUDE.md that auto-loads instructions, identity, preferences, active-context.
- Created memory-bank/ with 8 files using Chris's five-section taxonomy plus active-context and progress-log.
- Researched best patterns: Anthropic official memory docs, Cline Memory Bank, russbeye token-tuning.
- Committed and pushed to claude/kos-setup-rlf1c8.
- Open: decide whether to move this to a dedicated memory repo so it applies across all projects.
- Added token-efficiency playbook (memory-bank/token-efficiency.md) and terse output rules in CLAUDE.md.
- Installed graphify code knowledge graph tool. Built repo graph (104 nodes, 126 edges).
  Documented setup and query commands in memory-bank/tools.md. Gitignored graphify-out/.
- Clarified: graphify is a code knowledge graph, not the social-media content puller.
- Ran full /graphify semantic pipeline on the repo: 83 nodes, 119 edges, 10 communities.
  God nodes: Track, MusicBot, GuildQueue, Persistent Memory Bank, QueueManager.
  Committed graph.json + GRAPH_REPORT.md so future sessions query for ~0 tokens.
- Added SessionStart hook (.claude/hooks/session-start.sh + .claude/settings.json):
  every web session auto-installs graphify and sets PATH. Container resets, hook
  re-assembles in seconds. Functionally permanent, automatic. Validated, exit 0.
- Installed and documented claude-mem (npx claude-mem install). Works on local
  Claude Code, not cloud sessions (machine-local store, container wipes). See tools.md.
