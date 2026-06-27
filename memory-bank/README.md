# Memory Bank

Persistent memory for Claude so it remembers Chris's projects, preferences, and
history across sessions instead of starting cold every time.

## Why this exists

Chris works in ephemeral web/cloud Claude Code sessions. The container is wiped
when it goes idle. Two things people assume persist actually do not here:

- Auto memory (`~/.claude/projects/.../memory/`) is machine-local. Anthropic docs:
  "Files are not shared across machines or cloud environments." Wiped between sessions.
- claude.ai memory (the work-context summary) is a separate feature Claude Code cannot write to.

So the only memory that survives is what is committed to this Git repo. That is
what this folder is. The root `CLAUDE.md` auto-loads the must-have files at the
start of every session.

## Layout

| File | What it holds | Loaded |
| --- | --- | --- |
| `instructions.md` | Rules Chris gave, kept verbatim | Every session |
| `identity.md` | Who Chris is | Every session |
| `preferences.md` | Communication and content style | Every session |
| `active-context.md` | What is in flight right now | Every session |
| `projects.md` | Zenthra, Clearcoat, KOS, JARVIS, with status | On demand |
| `career.md` | D1 track and field recruitment | On demand |
| `progress-log.md` | Dated session history | On demand |

The split is on purpose. Must-haves auto-load. Heavier reference files load only
when relevant, so the context window is not bloated every session.

## The update ritual

When Chris says "update memory bank", or after meaningful work, Claude should:

1. Update `active-context.md` to reflect the new current focus.
2. Add a dated entry to `progress-log.md` (newest at the bottom, format `YYYY-MM-DD`).
3. If a fact about identity, projects, career, or preferences changed, edit that file too.
4. Commit and push so it survives the session.

Keep entries short. One idea per line. Specific numbers over vague claims.

## Memory export format

When Chris asks for a memory export, output one code block with five ordered
sections: Instructions, Identity, Career, Projects, Preferences. Each entry on one
line as `[YYYY-MM-DD] - content` (or `[unknown]`), sorted oldest first within each
section. Preserve Chris's words verbatim for instructions and preferences. After
the block, state whether the export is complete or more remain.
