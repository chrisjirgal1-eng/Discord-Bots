#!/bin/bash
# Portable installer for Chris's Claude Code setup.
# Makes the rules, skills, and memory bank available to plain Claude Code (user-global)
# or to any other project repo (per-repo). Run from the discord-bots checkout.
#
# Usage:
#   tools/install-claude-setup.sh global          # install to ~/.claude (all projects, this machine)
#   tools/install-claude-setup.sh repo <path>     # install into another repo's .claude + memory-bank
#
# Idempotent. Safe to re-run. Does not delete anything you created.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"   # repo root (this script lives in tools/)
MODE="${1:-}"

die() { echo "error: $*" >&2; exit 1; }

copy_rules_and_skills() {
  local dest="$1"
  mkdir -p "$dest/rules" "$dest/skills"
  cp -R "$SRC/.claude/rules/." "$dest/rules/"
  cp -R "$SRC/.claude/skills/." "$dest/skills/"
}

install_global() {
  local dest="$HOME/.claude"
  echo "Installing to $dest (applies to every project + plain Claude Code on this machine)"
  copy_rules_and_skills "$dest"
  mkdir -p "$dest/memory-bank"
  cp -R "$SRC/memory-bank/." "$dest/memory-bank/"

  # User-level CLAUDE.md that loads the must-have memory for every session.
  # Append our managed block once; do not clobber an existing user CLAUDE.md.
  local md="$dest/CLAUDE.md"
  local marker="<!-- chris-setup:managed -->"
  if ! grep -qF "$marker" "$md" 2>/dev/null; then
    {
      echo ""
      echo "$marker"
      echo "@~/.claude/memory-bank/instructions.md"
      echo "@~/.claude/memory-bank/identity.md"
      echo "@~/.claude/memory-bank/preferences.md"
      echo "@~/.claude/memory-bank/active-context.md"
      echo "<!-- /chris-setup:managed -->"
    } >> "$md"
    echo "  appended managed memory block to $md"
  else
    echo "  managed memory block already present in $md (left as-is)"
  fi
  echo "Done. Rules, skills, and memory are now global."
  echo "Note: graphify and the VoltAgent subagents install per-session via the hook;"
  echo "run them once with: uv tool install graphifyy && graphify install --platform claude"
}

install_repo() {
  local target="$1"
  [ -n "$target" ] || die "repo mode needs a target path: install-claude-setup.sh repo <path>"
  [ -d "$target" ] || die "target is not a directory: $target"
  echo "Installing into repo: $target"
  copy_rules_and_skills "$target/.claude"
  mkdir -p "$target/memory-bank"
  cp -R "$SRC/memory-bank/." "$target/memory-bank/"
  if [ -f "$SRC/.claude/hooks/session-start.sh" ]; then
    mkdir -p "$target/.claude/hooks"
    cp "$SRC/.claude/hooks/session-start.sh" "$target/.claude/hooks/session-start.sh"
    chmod +x "$target/.claude/hooks/session-start.sh"
  fi
  echo "Done. Commit the .claude/ and memory-bank/ dirs in $target so they persist."
  echo "Add a SessionStart hook entry to $target/.claude/settings.json if not present."
}

case "$MODE" in
  global) install_global ;;
  repo)   install_repo "${2:-}" ;;
  *) cat <<EOF
Portable Claude Code setup installer.

  tools/install-claude-setup.sh global        Install to ~/.claude (all projects, this machine)
  tools/install-claude-setup.sh repo <path>   Install into another repo's .claude + memory-bank

Run from the discord-bots checkout.
EOF
     exit 1 ;;
esac
