#!/bin/bash
# SessionStart hook: re-assemble Chris's setup on every (ephemeral) web session.
# The container resets each session; this rebuilds the tooling in seconds so the
# committed memory bank + graphify knowledge graph are ready automatically.
set -euo pipefail

# Only meaningful in Claude Code on the web (fresh container each time).
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Make ~/.local/bin (where uv tool installs land) available for the whole session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
export PATH="$HOME/.local/bin:$PATH"

# 1. Install graphify (code knowledge graph) if missing. Idempotent.
if ! command -v graphify >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    uv tool install graphifyy -q >/dev/null 2>&1 || true
  else
    pip install graphifyy -q >/dev/null 2>&1 \
      || pip install graphifyy -q --break-system-packages >/dev/null 2>&1 || true
  fi
fi

# 2. Install the /graphify skill into Claude config. Idempotent.
if command -v graphify >/dev/null 2>&1; then
  graphify install --platform claude >/dev/null 2>&1 || true
fi

# 3. Status line. The memory bank itself auto-loads via CLAUDE.md @imports;
#    this just confirms the tooling is ready and points at the committed graph.
if command -v graphify >/dev/null 2>&1 && [ -f graphify-out/graph.json ]; then
  echo "Setup ready: memory-bank auto-loaded, graphify installed, committed graph at graphify-out/graph.json (query with: graphify query \"...\")."
else
  echo "Setup ready: memory-bank auto-loaded. graphify not available this session."
fi
