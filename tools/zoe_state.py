#!/usr/bin/env python3
"""ZOE persistent continuity: memory/zoe_state.json.

Stores session context, last commands, workspace state, user preferences, and system mode.
Loaded on startup (restore prior session, or safe defaults if missing/corrupt) and rewritten
on every command and on shutdown. Python is the single writer; Electron reads it for restore.

Core rule: state I/O is best-effort and must NEVER break the command pipeline. Every function
swallows its own errors and falls back to safe defaults, so ZOE keeps running with or without it.
"""
import os, json, time, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ROOT, "memory")
STATE_FILE = os.path.join(STATE_DIR, "zoe_state.json")

DEFAULTS = {
    "version": 1,
    "system_mode": "online",                 # online | offline | error
    "session": {"started": None, "last_seen": None, "context": ""},
    "last_commands": [],                      # [{ts, text, action, handled}], newest last
    "workspace_state": {"last": None},
    "preferences": {"voice_id": None, "wake_words": ["zoe", "hey zoe"]},
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

def record_command(text, action, handled=None, workspace=None):
    """The 'state updated' step of the pipeline. Append a command, update workspace/mode."""
    try:
        st = load()
        st["last_commands"] = (st.get("last_commands", []) + [{
            "ts": time.strftime("%H:%M:%S"), "text": text,
            "action": action, "handled": handled,
        }])[-20:]
        if workspace:
            st.setdefault("workspace_state", {})["last"] = workspace
        save(st)
    except Exception:
        pass

def set_mode(mode):
    """Persist the system mode: online | offline | error."""
    try:
        st = load(); st["system_mode"] = mode; save(st)
    except Exception:
        pass

if __name__ == "__main__":
    # quick self-test / inspector
    print(json.dumps(load(), indent=2))
