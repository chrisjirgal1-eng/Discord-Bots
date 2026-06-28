#!/usr/bin/env python3
"""Zoe long-term memory: an Obsidian-compatible markdown vault.

The vault (vault/) is plain markdown + YAML frontmatter + [[wikilinks]], so Obsidian opens the
folder directly AND Claude Code can read/write the very same notes. This module is Zoe's safe
read/write API over it, and the bridge between the runtime state (memory/zoe_state.json) and
durable notes.

Layout:
  vault/index.md            dashboard (regenerated, links to everything)
  vault/sessions/*.md       one note per session, synced from zoe_state
  vault/notes/*.md          topical long-term notes ([[wikilinked]], curated)
  vault/log/commands.md     append-only command log

Public API (also exposed over HTTP by zoe_server.py):
  write(title, content, folder, tags)   -> POST /memory/write
  read(query)                           -> GET  /memory/read
  sync()                                -> POST /memory/sync     (zoe_state -> a session note)
  resume()                              -> GET  /session/resume  (last session + state summary)
  log_command(text, action, handled)    (the router calls this on every command)

Everything is best-effort and never raises, so memory can never break the command pipeline.
"""
import os, sys, json, time, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.environ.get("ZOE_VAULT") or os.path.join(ROOT, "vault")

def _ensure():
    for d in ("", "sessions", "notes", "log"):
        try: os.makedirs(os.path.join(VAULT, d), exist_ok=True)
        except Exception: pass

def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "note").lower()).strip("-")[:60] or "note"

def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def _read(path):
    try:
        with open(path, encoding="utf-8") as f: return f.read()
    except Exception:
        return ""

def _write(path, text):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f: f.write(text)
        return True
    except Exception:
        return False

def _append(path, text):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f: f.write(text)
        return True
    except Exception:
        return False

def write(title, content, folder="notes", tags=None):
    """Create or overwrite a structured note. Returns its vault-relative path."""
    _ensure()
    rel = os.path.join(folder, _slug(title) + ".md")
    fm = ["---", f"title: {title}", f"created: {_now()}",
          "tags: [" + ", ".join(tags or []) + "]", "---", ""]
    _write(os.path.join(VAULT, rel), "\n".join(fm) + (content or "").rstrip() + "\n")
    _build_index()
    return rel.replace("\\", "/")

def read(query=None):
    """No query -> the index. A note name -> that note. Otherwise -> search matches."""
    _ensure()
    if not query:
        idx = _read(os.path.join(VAULT, "index.md")) or _build_index()
        return {"path": "index.md", "content": idx}
    for folder in ("notes", "sessions", "log", ""):
        p = os.path.join(VAULT, folder, _slug(query) + ".md")
        if os.path.exists(p):
            return {"path": os.path.relpath(p, VAULT).replace("\\", "/"), "content": _read(p)}
    return {"query": query, "matches": search(query)}

def search(term):
    term = (term or "").lower()
    out = []
    for p in glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True):
        txt = _read(p)
        if term in txt.lower() or term in os.path.basename(p).lower():
            i = txt.lower().find(term)
            snip = (txt[max(0, i - 60):i + 100] if i >= 0 else txt[:140]).replace("\n", " ")
            out.append({"path": os.path.relpath(p, VAULT).replace("\\", "/"), "snippet": snip.strip()})
    return out[:20]

def sync():
    """Push the current runtime state into a dated session note + refresh the index. Returns path."""
    _ensure()
    st = _load_state()
    sess = st.get("session", {}) or {}
    cmds = (st.get("history", {}) or {}).get("last_commands", []) or st.get("last_commands", [])
    ws = (st.get("workspace_state", {}) or {}).get("last")
    stamp = time.strftime("%Y-%m-%d-%H%M")
    lines = ["---", f"title: Session {stamp}", f"created: {_now()}", "tags: [session]", "---", "",
             f"# Session {stamp}", "",
             f"- mode: {st.get('system_mode', '?')}",
             f"- last workspace: {ws or '-'}",
             f"- started: {sess.get('started', '-')}  ·  last active: {sess.get('last_active', '-')}",
             "", "## Commands this session", ""]
    for c in cmds[-40:]:
        ok = "x" if c.get("handled") else " "
        lines.append(f"- [{ok}] `{c.get('ts', '')}` {c.get('text', '')} -> {c.get('action', '')}"
                     + (f" - {c.get('summary')}" if c.get("summary") else ""))
    rel = f"sessions/session-{stamp}.md"
    _write(os.path.join(VAULT, rel), "\n".join(lines) + "\n")
    _build_index()
    return rel.replace("\\", "/")

def resume():
    """Resume-last-state: the newest session note plus a one-glance state summary."""
    _ensure()
    sessions = sorted(glob.glob(os.path.join(VAULT, "sessions", "*.md")))
    last = sessions[-1] if sessions else None
    st = _load_state()
    cmds = (st.get("history", {}) or {}).get("last_commands", []) or st.get("last_commands", [])
    return {
        "system_mode": st.get("system_mode"),
        "last_workspace": (st.get("workspace_state", {}) or {}).get("last"),
        "last_command": (cmds[-1].get("text") if cmds else None),
        "command_count": len(cmds),
        "last_session_note": (os.path.relpath(last, VAULT).replace("\\", "/") if last else None),
        "last_session_content": (_read(last) if last else ""),
    }

def log_command(text, action, handled=True, summary=None):
    """Append every executed command to the vault command log (Part 3 requirement)."""
    line = (f"- `{_now()}` [{'ok' if handled else 'fail'}] **{action}** - {text}"
            + (f"  ({summary})" if summary else "") + "\n")
    _append(os.path.join(VAULT, "log", "commands.md"), line)

def _load_state():
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import zoe_state
        return zoe_state.load()
    except Exception:
        try:
            with open(os.path.join(ROOT, "memory", "zoe_state.json"), encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

def _build_index():
    _ensure()
    notes = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(VAULT, "notes", "*.md")))
    sessions = sorted((os.path.basename(p)[:-3] for p in glob.glob(os.path.join(VAULT, "sessions", "*.md"))),
                      reverse=True)
    lines = ["# Zoe Memory Vault", "",
             "Long-term memory for Zoe and Claude. Open this folder as an Obsidian vault.", "",
             "## Recent sessions", ""]
    lines += [f"- [[sessions/{s}|{s}]]" for s in sessions[:12]] or ["- (none yet)"]
    lines += ["", "## Notes", ""]
    lines += [f"- [[notes/{n}|{n}]]" for n in notes] or ["- (none yet)"]
    lines += ["", "## Log", "", "- [[log/commands|command log]]", ""]
    content = "\n".join(lines)
    _write(os.path.join(VAULT, "index.md"), content)
    return content

if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "resume"
    arg = " ".join(sys.argv[2:])
    if op == "read":     print(json.dumps(read(arg or None), indent=2))
    elif op == "write":  print(write(arg or "note", "Written from the CLI at " + _now()))
    elif op == "sync":   print(sync())
    elif op == "resume": print(json.dumps(resume(), indent=2))
    elif op == "log":    log_command(arg, "manual"); print("logged")
    else:                print(json.dumps(read(None), indent=2))
