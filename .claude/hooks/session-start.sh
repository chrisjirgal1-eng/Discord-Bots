#!/bin/bash
# SessionStart hook: the single auto-setup script for Chris's cloud sessions.
#
# Cloud containers reset every session. This rebuilds the whole tooling stack in
# the background so the committed memory bank + graphify knowledge graph are ready
# automatically, with no manual steps and no added startup wait.
#
# TO ADD A NEW TOOL: append a new "=== Tool: <name> ===" block in the section below.
# Keep each block idempotent (safe to run every session) and non-interactive.
set -euo pipefail

# Non-remote (local machine): nothing to do, return immediately.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Async: the session starts instantly; everything below runs in the background.
echo '{"async": true, "asyncTimeout": 300000}'

# ---------------------------------------------------------------------------
# Everything below this line runs in the background after the session starts.
# ---------------------------------------------------------------------------

# Make ~/.local/bin (uv tool install target) available for the whole session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
export PATH="$HOME/.local/bin:$PATH"

# === Tool: graphify (code knowledge graph) ===
# Lets Claude query the committed graph instead of reading every file. Idempotent.
if ! command -v graphify >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    uv tool install graphifyy -q >/dev/null 2>&1 || true
  else
    pip install graphifyy -q >/dev/null 2>&1 \
      || pip install graphifyy -q --break-system-packages >/dev/null 2>&1 || true
  fi
fi
if command -v graphify >/dev/null 2>&1; then
  graphify install --platform claude >/dev/null 2>&1 || true
fi

# === Tool: claude-mem (automatic session memory) ===
# Intentionally NOT installed here. claude-mem is local-machine only: its store
# lives in ~/.claude-mem and its worker/browser UI (localhost:37700) have no home
# in an ephemeral cloud container, so it cannot persist across web sessions.
# Run `npx claude-mem install` on a local machine instead. See memory-bank/tools.md.

# === Add new auto-setup tools below, one block each ===

exit 0
