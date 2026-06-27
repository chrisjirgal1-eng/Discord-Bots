<!-- This file loads at the start of every Claude Code session. Keep it lean (<200 lines). -->
<!-- Detail lives in memory-bank/. Only the must-haves are auto-imported below. -->

# Working with Chris

This repo carries Chris's persistent memory bank so Claude remembers across sessions.
In ephemeral web/cloud sessions, only committed files survive. This is the durable memory.

## Auto-loaded every session

@memory-bank/instructions.md
@memory-bank/identity.md
@memory-bank/preferences.md
@memory-bank/active-context.md

## Output style (conserve tokens)

- No preambles ("Great question", "Sure"). No closings ("Hope this helps").
- Do not restate the question before answering. Answer it.
- Short lines. One idea per line. Cut filler.
- Token-saving playbook: `memory-bank/token-efficiency.md`.

## Read on demand (not auto-loaded, saves context)

When the work calls for it, read these:

- `memory-bank/projects.md` - Zenthra, Clearcoat Co., KOS, JARVIS, with live status
- `memory-bank/career.md` - D1 track and field recruitment
- `memory-bank/progress-log.md` - dated session history
- `memory-bank/token-efficiency.md` - how to conserve tokens
- `memory-bank/tools.md` - graphify code knowledge graph, setup and query commands
- `memory-bank/README.md` - how this memory bank works and how to update it

## The one ritual that keeps this alive

When Chris says "update memory bank" (or at the end of meaningful work), update
`active-context.md` and add a dated entry to `progress-log.md`.
Commit and push those changes so they survive the session. A memory bank that
is not maintained drifts from reality and starts misleading. See `memory-bank/README.md`.
