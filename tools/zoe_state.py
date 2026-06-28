#!/usr/bin/env python3
"""ZOE persistent continuity: memory/zoe_state.json.

Stores session context, last commands, workspace state, user preferences, and system mode.
Loaded on startup (restore prior session, or safe defaults if missing/corrupt) and rewritten
on every command and on shutdown. Python is the single writer; Electron reads it for restore.

Core rule: state I/O is best-effort and must NEVER break the command pipeline. Every function
swallows its own errors and falls back to safe defaults, so ZOE keeps running with or without it.
"""
import os, sys, json, time, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_versions
    _SCHEMA = zoe_versions.SYSTEM["state_schema_version"]
except Exception:
    _SCHEMA = "1.0.0"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ROOT, "memory")
STATE_FILE = os.path.join(STATE_DIR, "zoe_state.json")

# Locked state contract (state_schema_version 1.0.0). New keys are additive only; legacy keys
# (version, system_mode, last_commands, workspace_state, preferences) are KEPT so older readers
# -- including the Electron HUD -- keep working. Unknown saved fields are preserved on load.
DEFAULTS = {
    "version": 1,                             # legacy marker (kept; never removed)
    "schema_version": _SCHEMA,                # versioned state contract
    "system_mode": "online",                  # legacy mirror of session.mode (online|offline|error)
    "session": {
        "started": None, "last_seen": None, "context": "",   # legacy fields (kept)
        "mode": "online", "workspace": {}, "last_active": "", "trace_log": [],
    },
    "history": {"last_commands": [], "max_entries": 50},      # FIFO, capped
    "last_commands": [],                      # legacy mirror (kept for old readers / the HUD)
    "workspace_state": {"last": None},        # legacy
    "preferences": {"voice_id": None, "wake_words": ["zoe", "hey zoe"]},
    "plugins": {"active": [], "registry": {}},
}

def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out

def load():
    """Return the saved state merged over defaults, or safe defaults if missing/corrupt."""
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return _merge(DEFAULTS, json.load(f))
    except Exception:
        return dict(DEFAULTS)

def save(state):
    """Atomically write the state. Best-effort; returns True on success."""
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        state = _merge(DEFAULTS, state or {})
        state.setdefault("session", {})["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
        fd, tmp = tempfile.mkstemp(dir=STATE_DIR, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, STATE_FILE)           # atomic on Windows + POSIX
        return True
    except Exception:
        return False

def start_session(context=""):
    """Load prior state and stamp a new session start. Returns the restored state."""
    st = load()
    st.setdefault("session", {})
    st["session"]["started"] = time.strftime("%Y-%m-%d %H:%M:%S")
    if context:
        st["session"]["context"] = context
    save(st)
    return st

def record_command(text, action, handled=None, workspace=None, trace_id=None, summary=None):
    """The 'state updated' step of the pipeline. Append to history (FIFO, capped at max_entries)
    and update workspace/last_active. Keeps the legacy last_commands list populated too.
    summary is the human-readable parsed intent, shown in the command-bar history panel."""
    try:
        st = load()
        entry = {"ts": time.strftime("%H:%M:%S"), "text": text, "action": action,
                 "handled": handled, "trace_id": trace_id, "summary": summary}
        hist = st.setdefault("history", {"last_commands": [], "max_entries": 50})
        cap = int(hist.get("max_entries", 50) or 50)
        hist["last_commands"] = (hist.get("last_commands", []) + [entry])[-cap:]
        st["last_commands"] = (st.get("last_commands", []) + [entry])[-20:]   # legacy mirror
        if workspace:
            st.setdefault("workspace_state", {})["last"] = workspace
            st.setdefault("session", {}).setdefault("workspace", {})["last"] = workspace
        st.setdefault("session", {})["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save(st)
    except Exception:
        pass

def set_mode(mode):
    """Persist the system mode: online | offline | error (legacy + session.mode mirror)."""
    try:
        st = load()
        st["system_mode"] = mode
        st.setdefault("session", {})["mode"] = mode
        save(st)
    except Exception:
        pass

if __name__ == "__main__":
    # quick self-test / inspector
    print(json.dumps(load(), indent=2))
