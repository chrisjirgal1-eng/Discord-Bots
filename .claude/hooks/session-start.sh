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

# === Tool: VoltAgent subagents (154 specialist subagents) ===
# Marketplace: VoltAgent/awesome-claude-code-subagents. git clone of third-party
# repos is blocked in this network, so fetch the tarball with curl and add it as a
# local directory marketplace, then install all 10 bundles. Idempotent.
if command -v claude >/dev/null 2>&1; then
  VOLT_DIR="$HOME/.volt-subagents"
  if [ ! -f "$VOLT_DIR/.claude-plugin/marketplace.json" ]; then
    mkdir -p "$VOLT_DIR"
    curl -sSL "https://codeload.github.com/VoltAgent/awesome-claude-code-subagents/tar.gz/refs/heads/main" \
      | tar -xz -C "$VOLT_DIR" --strip-components=1 >/dev/null 2>&1 || true
  fi
  if [ -f "$VOLT_DIR/.claude-plugin/marketplace.json" ]; then
    claude plugin marketplace add "$VOLT_DIR" >/dev/null 2>&1 || true
    for p in voltagent-core-dev voltagent-lang voltagent-infra voltagent-qa-sec \
             voltagent-data-ai voltagent-dev-exp voltagent-domains voltagent-biz \
             voltagent-meta voltagent-research; do
      claude plugin install "$p@voltagent-subagents" >/dev/null 2>&1 || true
    done
  fi
fi

# === Tool: claude-video (watch streaming / video links) ===
# Marketplace: bradautomates/claude-video. The watch plugin downloads a video with
# yt-dlp, extracts frames, and transcribes with whisper so a pasted video URL can be
# analyzed. git clone is blocked, so use the curl tarball. Needs yt-dlp + ffmpeg;
# this container ships neither, so install yt-dlp and a static ffmpeg.
if command -v claude >/dev/null 2>&1; then
  CV_DIR="$HOME/.claude-video-src"
  if [ ! -f "$CV_DIR/.claude-plugin/marketplace.json" ]; then
    mkdir -p "$CV_DIR"
    curl -sSL "https://codeload.github.com/bradautomates/claude-video/tar.gz/refs/heads/main" \
      | tar -xz -C "$CV_DIR" --strip-components=1 >/dev/null 2>&1 || true
  fi
  if [ -f "$CV_DIR/.claude-plugin/marketplace.json" ]; then
    claude plugin marketplace add "$CV_DIR" >/dev/null 2>&1 || true
    claude plugin install watch@claude-video >/dev/null 2>&1 || true
  fi
  command -v yt-dlp >/dev/null 2>&1 || uv tool install yt-dlp -q >/dev/null 2>&1 || true
  if ! command -v ffmpeg >/dev/null 2>&1; then
    pip install imageio-ffmpeg -q --break-system-packages >/dev/null 2>&1 || true
    FF="$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || true)"
    [ -n "$FF" ] && ln -sf "$FF" "$HOME/.local/bin/ffmpeg" 2>/dev/null || true
  fi
fi

# === Add new auto-setup tools below, one block each ===

exit 0
