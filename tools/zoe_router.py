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
import os, sys, json, time, uuid, re, subprocess, webbrowser, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_state          # persistent continuity; optional, never blocks routing
except Exception:
    zoe_state = None
try:
    import zoe_memory         # Obsidian long-term memory; optional, best-effort
except Exception:
    zoe_memory = None
try:
    import zoe_learn          # learned-corrections store (memory/learned_routes.json); best-effort
except Exception:
    zoe_learn = None
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
GROQ_MODEL = "llama-3.1-8b-instant"   # fast classifier (~3-5x quicker than 70b; classification is simple)
DEFAULT_CONTROL = "http://127.0.0.1:7766"

INTENT_SYS = (
    "You are Zoe's command router on Chris's Windows PC. Reply with ONLY a JSON object: "
    '{"action": "workspace|launch|close|folder|web|memory|agent|research|chat", "target": "", "url": "", "say": ""}. '
    "- memory: recall from Chris's saved notes / knowledge vault. Use for 'what do I know about X', "
    "'what do I have on X', 'what did I learn/save about X', 'recall X', 'look up X in my notes', "
    "'show my notes/research on X', 'who are my creators', as well as 'what did I say/do last session' "
    "and 'what did we work on'. Prefer memory over chat whenever he asks what HE knows/saved/researched. "
    "target = the topic to recall (e.g. 'instagram creators', 'reels', 'hooks'), or empty for the last session. "
    "- agent: hand a hard reasoning, research, or multi-step coding task to the Hermes agent. Use "
    "when he says 'ask hermes', 'have hermes', or for a complex task beyond a simple command. "
    "target = the full request. "
    "- research: break down a specific VIDEO or REEL for viral hooks, structure, pacing, and why "
    "it worked, using VaultOS. Use for 'research this video', 'break down this reel/short', "
    "'analyze this youtube video' when a video/reel URL is present. url = the video URL. "
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

# --- local fast-path: unambiguous commands skip the LLM entirely (instant). Only HIGH-confidence
# patterns belong here; anything not matched falls through to the (now fast) Groq classifier.
_FAST_MEM = re.compile(r"(?:what do i know about|what did i (?:learn|save|research|note) about|"
                       r"recall|look up|pull up my notes on|show my (?:notes|research) on)\s+(.+)", re.I)
_FAST_WS = re.compile(r"\b(coding|developer|dev|gaming|editing|video|school|study)\s+(?:mode|workspace|setup)\b"
                      r"|\bstart\s+(coding|gaming|editing|school|study)\b", re.I)
_FAST_CLOSE = re.compile(r"^\s*(?:hey\s+)?(?:zoe[,!.]?\s+)?(?:close|quit|kill|shut\s+down|exit)\s+(.+?)[.?!]*\s*$", re.I)
_FAST_LAUNCH = re.compile(r"^\s*(?:hey\s+)?(?:zoe[,!.]?\s+)?(?:launch|fire\s+up|boot\s+up)\s+(.+?)[.?!]*\s*$", re.I)


def _fast_classify(text):
    t = (text or "").strip()
    if not t:
        return None
    m = _FAST_MEM.search(t)
    if m:
        return {"action": "memory", "target": m.group(1).strip(" ?.!"), "say": ""}
    m = _FAST_WS.search(t)
    if m:
        name = (m.group(1) or m.group(2) or "that").lower()
        return {"action": "workspace", "target": t, "say": f"Starting {name} mode, sir."}
    m = _FAST_CLOSE.match(t)
    if m:
        tgt = m.group(1).strip()
        return {"action": "close", "target": tgt, "say": f"Closing {tgt}, sir."}
    m = _FAST_LAUNCH.match(t)
    if m:
        tgt = m.group(1).strip()
        return {"action": "launch", "target": tgt, "say": f"Opening {tgt}, sir."}
    return None


# --- conversation context resolution (Phase 1) ----------------------------------------------
_REVERSIBLE = {"launch": "close", "close": "launch"}
_RE_ACTUALLY = re.compile(r"^\s*(?:actually|no[, ]+|wait[, ]+|make it|instead|change it to|rather)\s+(.+)$", re.I)
_RE_AGAIN    = re.compile(r"\b(?:do (?:that|it) again|again|same(?: thing)?|repeat that|once more)\b", re.I)
_RE_UNDO     = re.compile(r"\b(?:undo(?: that| it)?|never ?mind that|reverse that|cancel that|take that back)\b", re.I)
_RE_CONTINUE = re.compile(r"^\s*(?:continue|keep going|resume|go on|carry on|tell me more|more on (?:that|it)|and then)\b", re.I)
_RE_WRONG    = re.compile(r"(?:that'?s not what i meant|that'?s wrong|not what i (?:said|wanted|meant)|you misunderstood)", re.I)


def _resolve_context(text, conv):
    """Resolve a referential follow-up ('again', 'actually X', 'undo it', 'continue', 'wrong')
    against the live conversation state. Returns an action dict to short-circuit classify, or
    None to pass through. Best-effort, never raises."""
    try:
        t = (text or "").strip(); low = t.lower()
        last = (conv or {}).get("last_action") or {}
        la, ltgt = last.get("action"), last.get("target")
        if _RE_WRONG.search(low):
            return {"action": "chat", "say": "My apologies, sir. What did you mean?",
                    "_correction": last.get("text"), "_ctx": "wrong"}
        m = _RE_ACTUALLY.match(t)
        if m and la in ("launch", "close", "folder", "workspace"):
            newt = m.group(1).strip(" .?!")
            return {"action": la, "target": newt, "say": f"Switching to {newt}, sir.", "_ctx": "swap"}
        if _RE_AGAIN.search(low) and la and ltgt:
            return {"action": la, "target": ltgt, "url": last.get("url"),
                    "say": "On it again, sir.", "_ctx": "repeat"}
        if _RE_UNDO.search(low) and last.get("reversible") and ltgt and _REVERSIBLE.get(la):
            return {"action": _REVERSIBLE[la], "target": ltgt, "say": "Undoing that, sir.", "_ctx": "undo"}
        if _RE_CONTINUE.match(t):
            topic = (conv or {}).get("current_topic")
            if topic:
                return {"action": "memory", "target": topic, "say": "", "_ctx": "continue"}
        return None
    except Exception:
        return None


def _conv_summary(conv):
    """One-line context hint fed to the classifier so incomplete requests fill from context."""
    if not conv:
        return ""
    bits = []
    if conv.get("current_topic"):   bits.append(f"current topic: {conv['current_topic']}")
    if conv.get("last_target"):     bits.append(f"last referenced: {conv['last_target']}")
    if conv.get("current_project"): bits.append(f"current project: {conv['current_project']}")
    return ("Conversation context (use to fill in vague/incomplete requests): "
            + "; ".join(bits) + ".") if bits else ""


_RE_TEACH = re.compile(
    r"^\s*(?:when(?:ever)? i say|if i say|remember (?:that )?)\s*['\"]?(.+?)['\"]?\s*"
    r"(?:,|then|it means|means|do|open|run|launch|that'?s)\s+(.+)$", re.I)


def _teach(text, groq_key=None, history=None, conv=None):
    """Explicit teaching: 'when I say X, do Y' -> learn X -> classify(Y). Returns a confirmation
    chat action, or None if not a teaching phrase. Best-effort, never raises."""
    if not zoe_learn:
        return None
    try:
        m = _RE_TEACH.match((text or "").strip())
        if not m:
            return None
        phrase, target = m.group(1).strip(" .?!'\""), m.group(2).strip(" .?!'\"")
        if not phrase or not target:
            return None
        learned = classify(target, groq_key, history, conv)
        if learned.get("action") in (None, "", "chat"):
            return {"action": "chat", "_taught": None,
                    "say": f"I'm not sure how to '{target}', sir — give me a clear command to map it to."}
        zoe_learn.learn(phrase, learned, source="taught")
        what = (learned.get("target") or learned.get("url") or "").strip()
        return {"action": "chat", "_taught": phrase,
                "say": f"Got it, sir. From now on '{phrase}' will {learned['action']} {what}.".strip()}
    except Exception:
        return None


def classify(text, groq_key, history=None, conv=None):
    """Phrase -> action dict. Common, unambiguous commands are matched locally (instant, no LLM
    round-trip); everything else goes to a fast Groq model, enriched with conversation context."""
    fast = _fast_classify(text)
    if fast:
        return fast
    sysmsgs = [{"role": "system", "content": INTENT_SYS}]
    ctx = _conv_summary(conv)
    if ctx:
        sysmsgs.append({"role": "system", "content": ctx})
    msgs = sysmsgs + (history or [])[-4:] + [{"role": "user", "content": text}]
    try:
        raw = _groq(msgs, groq_key, max_tokens=120)
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

def _explain(action):
    """Turn an action dict into a human-readable parsed intent + ordered steps (for the command
    bar's explain view). Pure, no side effects."""
    a = action.get("action", "chat")
    target = action.get("target", "")
    url = action.get("url", "")
    if a == "launch":
        return f"Launch the app '{target}'", [f"Resolve '{target}' to an app", f"Launch {target}"]
    if a == "close":
        return f"Close '{target}'", [f"Find the {target} process", f"Close {target}"]
    if a == "folder":
        return f"Open the folder '{target}'", [f"Locate {target}", "Open it in Explorer"]
    if a == "web":
        return f"Open the browser to {url}", ["Open the default browser", f"Navigate to {url}"]
    if a == "workspace":
        return (f"Start the '{target}' workspace",
                [f"Load workspace '{target}'", "Launch its apps and sites in order"])
    if a == "memory":
        return "Recall from long-term memory", ["Search the Obsidian vault", "Return what was found"]
    if a == "agent":
        return "Hand off to the Hermes agent", ["Send the request to Hermes", "Return its answer"]
    if a == "research":
        return (f"Research the video {url or target}",
                ["Download + transcribe", "Extract hook / structure / score", "Save to the vault"])
    return "Answer in conversation", ["Understand the request", "Compose a reply"]

def _recall(text, action):
    """Memory action: recall / show memory / what did I say last session. Returns (handled, say, data)."""
    q = (action.get("target") or "").strip()
    low = text.lower()
    if (not q or "last session" in low or "last time" in low or "what did i" in low
            or "show memory" in low or "what did we" in low):
        mem = zoe_memory.resume()
        n = mem.get("command_count", 0)
        last = mem.get("last_command")
        say = (f"Last session you ran {n} command" + ("s" if n != 1 else "")
               + (f"; the most recent was '{last}'." if last else "."))
        return True, say, mem
    mem = zoe_memory.read(q)
    if mem.get("matches"):
        say = f"I found {len(mem['matches'])} memory note(s) about {q}, sir."
    elif mem.get("content"):
        say = f"Here is your note on {q}, sir."
    else:
        say = f"I have nothing in memory about {q} yet, sir."
    return True, say, mem

def process(text, source="ui", groq_key=None, ctrl=None, history=None, simulate=False):
    """THE shared command pipeline. Voice and the command bar both call this -- one engine, no
    duplicate logic. Classify -> explain -> execute -> record. Returns a rich, explainable result
    ({parsed, steps, intent, handled, status, say, trace_id, ...}). Never raises."""
    groq_key = groq_key or os.environ.get("GROQ_API_KEY")
    tid = uuid.uuid4().hex
    memory = None
    agent_result = None
    trace = []                                            # live, timed, per-step execution log
    t0 = time.perf_counter()
    def step(label, status, since=None):
        trace.append({"label": label, "status": status,
                      "ms": round((time.perf_counter() - since) * 1000) if since else 0})
    try:
        conv = zoe_state.get_conversation() if zoe_state else {}
    except Exception:
        conv = {}
    try:
        ts = time.perf_counter()
        taught = _teach(text, groq_key, history, conv)                       # "when I say X, do Y" -> learn it
        learned = None if taught else (zoe_learn.lookup(text) if zoe_learn else None)
        action = taught or learned or _resolve_context(text, conv) or classify(text, groq_key, history, conv)
        a = action.get("action", "chat")
        step(("Taught a new rule" if taught else "Applied a learned correction" if learned
              else "Resolved from context" if action.get("_ctx") else "Understanding the request"), "done", ts)
        parsed, steps = _explain(action)
        step("Parsed intent: " + parsed, "done")
        if a == "memory" and zoe_memory:
            ts = time.perf_counter()
            handled, say, memory = _recall(text, action)   # recall, no side effects
            for s in steps: step(s, "done" if handled else "fail")
            step("Recalled from long-term memory", "done" if handled else "fail", ts)
        elif a == "agent":
            ts = time.perf_counter()
            cmd = make_command(intent="plugin_action", target="hermes",
                               payload={"prompt": action.get("target") or text})
            handled, res = _run_plugin(cmd)
            ans = res.get("answer") if isinstance(res, dict) else None
            err = res.get("error") if isinstance(res, dict) else None
            agent_result = {"agent": "hermes", "answer": ans, "error": err}
            say = (ans[:240] if ans else (err or "Hermes had no answer, sir."))
            for s in steps: step(s, "done" if handled else "fail")
            step("Hermes responded" if handled else "Hermes unavailable", "done" if handled else "fail", ts)
        elif a == "research":
            ts = time.perf_counter()
            vurl = action.get("url") or action.get("target") or text
            cmd = make_command(intent="plugin_action", target="vaultos", payload={"url": vurl})
            handled, res = _run_plugin(cmd)
            say = (res.get("say") if isinstance(res, dict) else None) or (
                "Saved a breakdown to the vault, sir." if handled else "I couldn't research that, sir.")
            for s in steps: step(s, "done" if handled else "fail")
            step("VaultOS breakdown saved" if handled else "VaultOS could not process it",
                 "done" if handled else "fail", ts)
        elif simulate:
            handled, say = True, action.get("say", "On it, sir.")
            for s in steps: step(s, "done")
            step("Simulated - no side effects", "done")
        else:
            ts = time.perf_counter()
            a, handled = execute(action, text, ctrl)
            for s in steps: step(s, "done" if handled else "fail")
            step("Executing the action", "done" if handled else "fail", ts)
            say = action.get("say", "On it, sir.")
        step("Completed" if handled else "Could not complete (recovered safely)",
             "done" if handled else "fail", t0)
    except Exception as e:
        action, parsed, steps = {}, "Could not parse that", ["Parse the request"]
        a, handled, say = "chat", False, "Sorry sir, something went wrong."
        step("Error - " + str(e)[:50], "fail", t0)
    if zoe_state:
        try:
            topic = action.get("target") if a in ("memory", "research", "web") else None
            zoe_state.record_command(text, a, handled, trace_id=tid, summary=parsed,
                                     workspace=action.get("target") if a == "workspace" else None,
                                     target=action.get("target"), url=action.get("url"), topic=topic)
            if action.get("_correction"):                       # "that's not what I meant"
                zoe_state.add_correction(text, action.get("_correction"))
                zoe_state.update_conversation(pending_correction=action.get("_correction"))
            elif (handled and zoe_learn and conv.get("pending_correction")
                  and not action.get("_taught") and not action.get("_learned") and a != "chat"):
                zoe_learn.learn(conv["pending_correction"], action, source="correction")  # implicit learn
                zoe_state.update_conversation(pending_correction=None)
        except Exception:
            pass
    if zoe_memory:                                          # log every command to the vault
        try: zoe_memory.log_command(text, a, handled, summary=parsed)
        except Exception: pass
    out = {
        "schema_version": COMMAND_SCHEMA_VERSION, "trace_id": tid, "source": source,
        "text": text, "intent": a, "parsed": parsed, "steps": steps,
        "target": action.get("target", ""), "url": action.get("url", ""),
        "handled": bool(handled), "say": say,
        "status": "completed" if handled else "failed",
        "trace": trace, "timing_ms": round((time.perf_counter() - t0) * 1000),
    }
    if memory is not None:
        out["memory"] = memory
    if agent_result is not None:
        out["agent"] = agent_result
    return out

def handle(text, groq_key, ctrl=None, history=None):
    """Voice entry point. Delegates to process() (the shared engine) and returns (say, action)."""
    r = process(text, "voice", groq_key, ctrl, history)
    return r["say"], r["intent"]


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
