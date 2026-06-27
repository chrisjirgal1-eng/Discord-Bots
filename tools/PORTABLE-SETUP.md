# Take this setup anywhere

This makes everything built here (rules, skills, memory bank) available to your other
projects and to plain Claude Code, not just the discord-bots repo.

## Two ways to install

### 1. Global (your computer, all projects)

Best for "normal Claude has everything I have." Installs to `~/.claude`, which every
Claude Code session on that machine reads, regardless of project.

```sh
tools/install-claude-setup.sh global
```

What it does:
- Copies `.claude/rules/` (model-routing, verification, learning) to `~/.claude/rules/`.
- Copies `.claude/skills/` (coach-email, caption, zen-announce, clearcoat-post) to `~/.claude/skills/`.
- Copies the memory bank to `~/.claude/memory-bank/`.
- Appends a managed block to `~/.claude/CLAUDE.md` that loads the must-have memory every session.
- Idempotent. Re-run anytime. Does not delete anything you made.

Then install the per-session tools once:

```sh
uv tool install graphifyy && graphify install --platform claude
```

### 2. Per-repo (another project, including cloud sessions)

Best when a specific repo needs the setup committed so it survives ephemeral cloud sessions.

```sh
tools/install-claude-setup.sh repo /path/to/other-repo
```

What it does:
- Copies rules, skills, memory bank, and the SessionStart hook into that repo.
- Commit `.claude/` and `memory-bank/` there so they persist.
- Register the hook in that repo's `.claude/settings.json` (copy the block from this repo).

## The honest caveat

- On a persistent machine, global install is permanent.
- In ephemeral cloud sessions, `~/.claude` resets, so for a cloud project use the per-repo
  install and commit the files. The SessionStart hook then rebuilds graphify and the
  VoltAgent subagents each session.

## What is portable vs not

| Piece | Portable how |
|---|---|
| Rules (routing, verification, learning) | Copied to ~/.claude/rules or the repo |
| Skills (coach-email, caption, ...) | Copied to ~/.claude/skills or the repo |
| Memory bank (who you are, projects, lessons) | Copied to ~/.claude/memory-bank or the repo |
| graphify, VoltAgent subagents | Reinstalled per session via the hook or the one-liners above |
| MCP connectors (GitHub, Supabase, ...) | Already global; auth lives in MCP config, not a repo |
