#!/usr/bin/env python3
"""Zoe command router: the ONE place that turns a phrase into an action.

This is the single source of command routing for Zoe's voice/AI engine. The voice loop
(zoe_assistant.py) captures speech and calls handle(); everything about WHAT a command
means and HOW it is dispatched lives here and nowhere else. See COMMAND_SYSTEM_GUIDE.md.

Action types (classify() decides, execute() dispatches):
  workspace  start a named workspace (Coding/School/Gaming/Editing)  -> Electron control /voice
  launch     open a desktop app                                      -> Electron /action {launch}, else `start`
  close      close a desktop app                                     -> Electron /action {close}
  folder     open a folder                                           -> Electron /action {folder}, else os.startfile
  web        open / search / show something in the browser           -> webbrowser.open(url)
  chat       plain conversation                                      -> just speak the reply

Native execution primitives live in the Electron app (electron/services/launcher.js and
workspaceManager.js), reached over the localhost control endpoint (env ZOE_CONTROL, default
http://127.0.0.1:7766). When Electron is not running, folder and launch fall back to Python
(os.startfile / start); workspace and close need the desktop app.
"""
import os, sys, json, subprocess, webbrowser, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_state          # persistent continuity; optional, never blocks routing
except Exception:
    zoe_state = None

GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_CONTROL = "http://127.0.0.1:7766"

INTENT_SYS = (
    "You are Zoe's command router on Chris's Windows PC. Reply with ONLY a JSON object: "
    '{"action": "workspace|launch|close|folder|web|chat", "target": "", "url": "", "say": ""}. '
    "- workspace: start a named workspace or mode (coding, school, gaming, editing). "
    "target = the workspace name or his exact phrase. "
    "- launch: open a desktop app. target = the app name (Discord, Spotify, VS Code, Notepad). "
    "- close: close or quit a desktop app. target = the app name. "
    "- folder: open a folder. target = a Windows path; map Downloads, Documents, Desktop, Videos, "
    "Pictures, Music to %USERPROFILE%\\\\<name>. "
    "- web: see, show, pull up, search, watch, or look something up. url = the best https URL "
    "(news -> https://news.google.com ; youtube -> https://www.youtube.com/results?search_query=QUERY ; "
    "otherwise https://www.google.com/search?q=QUERY, URL-encoded). "
    "- chat: plain conversation. "
    "Always set say to one short spoken sentence, address him as sir or Chris."
)

def _groq(messages, key, max_tokens=200):
    body = json.dumps({"model": GROQ_MODEL, "messages": messages,
                       "max_tokens": max_tokens, "temperature": 0.4}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "curl/8.19.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

def _post(ctrl, route, payload):
    """POST to the Electron control endpoint. Returns the parsed result, or None if unreachable."""
    if not ctrl:
        return None
    try:
        req = urllib.request.Request(ctrl.rstrip("/") + route,
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.load(r)
    except Exception:
        return None

def classify(text, groq_key, history=None):
    """Phrase -> action dict. The only place a command's meaning is decided."""
    msgs = [{"role": "system", "content": INTENT_SYS}] + (history or [])[-4:] + [{"role": "user", "content": text}]
    try:
        raw = _groq(msgs, groq_key)
        return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    except Exception:
        return {"action": "chat", "say": "Sorry sir, I didn't catch that."}

def execute(action, command, ctrl=None):
    """Dispatch an action dict. The only place actions run. Returns (action_type, handled)."""
    ctrl = ctrl or os.environ.get("ZOE_CONTROL") or DEFAULT_CONTROL
    a = action.get("action", "chat")
    target = action.get("target", "")
    url = action.get("url", "")
    handled = False
    if a == "workspace":
        r = _post(ctrl, "/voice", {"phrase": target or command})
        handled = bool(r and r.get("handled"))
    elif a == "launch":
        r = _post(ctrl, "/action", {"launch": target})
        if r and r.get("handled"):
            handled = True
        elif target:
            try: subprocess.Popen(["cmd", "/c", "start", "", target]); handled = True
            except Exception: pass
    elif a == "close":
        r = _post(ctrl, "/action", {"close": target})
        handled = bool(r and r.get("handled"))
    elif a == "folder":
        r = _post(ctrl, "/action", {"folder": target})
        if r and r.get("handled"):
            handled = True
        else:
            p = os.path.expandvars(target)
            if p and os.path.exists(p):
                try: os.startfile(p); handled = True
                except Exception: pass
    elif a == "web":
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            webbrowser.open(url); handled = True
    elif a == "chat":
        handled = True
    return a, handled

def handle(text, groq_key, ctrl=None, history=None):
    """Classify, execute, and record. Returns (spoken_reply, action_type). State update is the
    final pipeline step and is best-effort: it never blocks the command."""
    action = classify(text, groq_key, history)
    a, handled = execute(action, text, ctrl)
    if zoe_state:
        try:
            zoe_state.record_command(text, a, handled,
                                     workspace=action.get("target") if a == "workspace" else None)
        except Exception:
            pass
    return action.get("say", "On it, sir."), a
