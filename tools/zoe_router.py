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
import os, sys, json, time, uuid, subprocess, webbrowser, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_state          # persistent continuity; optional, never blocks routing
except Exception:
    zoe_state = None
try:
    import zoe_versions
    COMMAND_SCHEMA_VERSION = zoe_versions.SYSTEM["command_schema_version"]
    PLUGIN_API_VERSION = zoe_versions.SYSTEM["plugin_api_version"]
    _compatible = zoe_versions.compatible
except Exception:                # versions module optional; degrade, never fail
    COMMAND_SCHEMA_VERSION = "1.0.0"
    PLUGIN_API_VERSION = "1.0.0"
    def _compatible(a, b):
        return str(a).split(".")[0] == str(b).split(".")[0]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


# ----------------------------------------------------------------------------------------------
# Versioned kernel layer: the locked command schema, the plugin registry, and route() -- the ONE
# structured entry point any source (UI, voice, system, plugin) uses. classify()/execute()/handle()
# above remain the voice/AI path; route() is the structured-command path. Both live here, so the
# router stays the single source of routing. Everything below degrades gracefully, never crashes.
# ----------------------------------------------------------------------------------------------

# The locked command contract. Core keys never change; new fields go inside payload only.
_CORE_KEYS = ("schema_version", "source", "intent", "target", "action", "payload",
              "timestamp", "trace_id")

# intent (category) -> the existing execute() action vocabulary
_INTENT_TO_ACTION = {"open_app": "launch", "close_app": "close",
                     "navigate": "web", "system_action": "workspace"}

_PLUGINS = {}   # plugin_name -> {"meta": {...}, "execute": fn}

def make_command(source="ui", intent="unknown", target="", action="unknown", payload=None):
    """Build a command in the locked schema (fills schema_version, timestamp, trace_id)."""
    return {
        "schema_version": COMMAND_SCHEMA_VERSION,
        "source": source, "intent": intent, "target": target or "", "action": action,
        "payload": dict(payload) if isinstance(payload, dict) else {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "trace_id": uuid.uuid4().hex,
    }

def validate_command(command):
    """Normalize any input into the locked command schema. Missing core keys are filled, the
    caller's schema_version/timestamp/trace_id are kept (forward-compat), and any unknown
    top-level fields are tucked into payload._extra so nothing is lost. Never raises."""
    c = dict(command) if isinstance(command, dict) else {}
    out = make_command(
        source=c.get("source", "ui"),
        intent=c.get("intent", "unknown"),
        target=c.get("target", "") or "",
        action=c.get("action", "unknown"),
        payload=c.get("payload") if isinstance(c.get("payload"), dict) else {},
    )
    for k in ("schema_version", "timestamp", "trace_id"):
        if c.get(k):
            out[k] = c[k]
    for k, v in c.items():
        if k not in _CORE_KEYS:
            out["payload"].setdefault("_extra", {})[k] = v
    return out

def load_plugins(plugins_dir=None):
    """Scan the plugins folder, validate the contract, register the good ones. Each bad plugin is
    isolated and skipped; one failure never blocks the others or the system. Returns loaded names."""
    import importlib.util
    _PLUGINS.clear()
    pdir = plugins_dir or os.path.join(ROOT, "plugins")
    loaded = []
    try:
        files = [f for f in os.listdir(pdir) if f.endswith(".py") and not f.startswith("__")]
    except Exception:
        files = []
    for fn in files:
        try:
            spec = importlib.util.spec_from_file_location("zoe_plugin_" + fn[:-3],
                                                          os.path.join(pdir, fn))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            meta = getattr(mod, "PLUGIN", None)
            execfn = getattr(mod, "execute", None)
            if not isinstance(meta, dict) or not callable(execfn):
                continue
            if not all(k in meta for k in ("plugin_name", "plugin_version",
                                           "supported_intents", "schema_version")):
                continue
            if not _compatible(meta.get("schema_version"), PLUGIN_API_VERSION):
                continue          # incompatible plugin API -> skip (fallback), do not crash
            _PLUGINS[meta["plugin_name"]] = {"meta": meta, "execute": execfn}
            loaded.append(meta["plugin_name"])
        except Exception:
            continue              # isolate a broken plugin
    if zoe_state:
        try:
            st = zoe_state.load()
            st.setdefault("plugins", {})["active"] = loaded
            st["plugins"]["registry"] = {n: _PLUGINS[n]["meta"] for n in loaded}
            zoe_state.save(st)
        except Exception:
            pass
    return loaded

def _run_plugin(cmd):
    """Dispatch to a plugin by target name, else by supported intent. Returns (handled, result).
    A plugin exception is caught and isolated -- it can never crash the router."""
    name = cmd.get("target") or (cmd.get("payload") or {}).get("plugin")
    plug = _PLUGINS.get(name)
    if not plug:
        for p in _PLUGINS.values():
            if cmd.get("intent") in p["meta"].get("supported_intents", []):
                plug = p
                break
    if not plug:
        return False, {"error": "no_plugin", "target": name}
    try:
        resp = plug["execute"](cmd)
        if isinstance(resp, dict):
            return bool(resp.get("handled")), resp.get("result", resp)
        return False, {"error": "bad_plugin_response"}
    except Exception as e:
        return False, {"error": "plugin_exception", "plugin": name, "detail": str(e)}

def route(command, ctrl=None, simulate=False):
    """The single structured entry point. Validate -> map intent -> execute (or plugin) -> record.
    Returns {schema_version, trace_id, source, intent, handled, fallback, result}. Never raises;
    on any internal error it returns handled:false with a structured error (noop fallback)."""
    cmd = validate_command(command)
    trace_id = cmd["trace_id"]
    intent, target, payload = cmd["intent"], cmd["target"], cmd["payload"]
    fallback = not _compatible(cmd["schema_version"], COMMAND_SCHEMA_VERSION)
    handled, result = False, {}
    try:
        if intent == "plugin_action":
            handled, result = _run_plugin(cmd)
        elif intent in _INTENT_TO_ACTION:
            if intent == "navigate":
                action = {"action": "web", "url": payload.get("url") or target, "target": target}
            elif intent == "system_action" and payload.get("folder"):
                action = {"action": "folder", "target": payload.get("folder")}
            else:
                action = {"action": _INTENT_TO_ACTION[intent], "target": target}
            if simulate:
                handled, result = True, {"simulated": True, "action": action["action"],
                                         "target": action.get("target", "")}
            else:
                a, handled = execute(action, target, ctrl)
                result = {"action": a, "target": action.get("target", "")}
        else:
            handled, result = False, {"error": "unknown_intent", "intent": intent}
    except Exception as e:
        handled, result = False, {"error": "router_exception", "detail": str(e)}
    if zoe_state:
        try:
            zoe_state.record_command(target or intent, intent, handled, trace_id=trace_id,
                                     workspace=target if intent == "system_action" else None)
        except Exception:
            pass
    return {"schema_version": COMMAND_SCHEMA_VERSION, "trace_id": trace_id,
            "source": cmd["source"], "intent": intent, "handled": handled,
            "fallback": fallback, "result": result}

# Load plugins once at import so route() works immediately. Best-effort: a plugin folder that is
# missing or full of broken files never stops the router from importing.
try:
    load_plugins()
except Exception:
    pass
