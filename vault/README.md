# Zoe Memory Vault

This folder is Zoe's long-term memory, stored as plain markdown so it is **also an Obsidian vault**.
Open this `vault/` folder directly in Obsidian and it just works (frontmatter + `[[wikilinks]]`).

It is read and written by:
- **Zoe** (the assistant) via `tools/zoe_memory.py` and the HTTP API on the telemetry server.
- **Claude Code** — these are plain files, so Claude reads and edits the same notes.

## Structure
| Folder | What | Committed? |
|---|---|---|
| `index.md` | Dashboard, links to everything (auto-regenerated) | no (runtime) |
| `sessions/` | One note per Zoe session, synced from `memory/zoe_state.json` | no (runtime) |
| `notes/` | Curated long-term notes, `[[wikilinked]]` | yes |
| `log/commands.md` | Append-only log of every command Zoe ran | no (runtime) |

## API (tools/zoe_memory.py, also over HTTP)
- `write(title, content, folder, tags)` → `POST /memory/write`
- `read(query)` → `GET /memory/read?q=...` (note name, search term, or blank for the index)
- `sync()` → `POST /memory/sync` (writes the current session to a note)
- `resume()` → `GET /session/resume` (last session + a one-glance state summary)

CLI: `python tools/zoe_memory.py [read|write|sync|resume|log] <arg>`

## How it fits the rest of memory
This vault is the **durable, queryable** layer. It complements:
- `memory/zoe_state.json` — fast runtime state (last commands, workspace, mode); `sync()` snapshots it here.
- `memory-bank/*.md` — the project/identity memory bank Claude maintains.
