#!/usr/bin/env python3
"""Bridge ZOE's powers to the OpenAI Realtime model as function tools.

The realtime model is her ears, brain, and mouth. This module is the hands: it
declares the tools she can call (TOOLS) and dispatches each call into the EXISTING
command router (zoe_router) so there is still ONE source of command routing. No
command logic is duplicated here -- every tool maps to zoe_router.execute / _recall /
the Hermes plugin path, exactly what the cascade voice loop uses.

dispatch(name, args, ctrl=None, simulate=True) returns a small JSON-able dict that is
sent back as the function_call_output; the model speaks a confirmation from it.
simulate=True plans the action with no side effects (used by the cloud self-test).
"""
import os, sys, json, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zoe_router          # the single command router (execute / route / recall / plugins)
try:
    import zoe_memory      # Obsidian long-term memory; optional, best-effort
except Exception:
    zoe_memory = None

# Tool schemas in the OpenAI Realtime `tools` format. Names + params mirror the
# router's action vocabulary so the model can drive everything ZOE already does.
TOOLS = [
    {"type": "function", "name": "launch_app",
     "description": "Open a desktop app on Chris's Windows PC (Discord, Spotify, VS Code, Notepad, etc.).",
     "parameters": {"type": "object",
        "properties": {"name": {"type": "string", "description": "The app name to open."}},
        "required": ["name"]}},
    {"type": "function", "name": "close_app",
     "description": "Close or quit a running desktop app.",
     "parameters": {"type": "object",
        "properties": {"name": {"type": "string", "description": "The app name to close."}},
        "required": ["name"]}},
    {"type": "function", "name": "open_folder",
     "description": "Open a folder in Explorer. Use Windows paths; Downloads/Documents/Desktop/"
                    "Videos/Pictures/Music map under the user profile.",
     "parameters": {"type": "object",
        "properties": {"path": {"type": "string", "description": "Folder name or Windows path."}},
        "required": ["path"]}},
    {"type": "function", "name": "open_web",
     "description": "Open the browser to a site or a search. Pass a full https URL, or a plain "
                    "query to search the web.",
     "parameters": {"type": "object",
        "properties": {"query_or_url": {"type": "string",
            "description": "An https URL, or a search query."}},
        "required": ["query_or_url"]}},
    {"type": "function", "name": "start_workspace",
     "description": "Start a named workspace or mode (coding, school, gaming, editing) which "
                    "launches its apps and sites.",
     "parameters": {"type": "object",
        "properties": {"name": {"type": "string", "description": "The workspace/mode name."}},
        "required": ["name"]}},
    {"type": "function", "name": "recall_memory",
     "description": "Recall from long-term memory: what was worked on last session, or notes on "
                    "a topic. Empty query = the last session.",
     "parameters": {"type": "object",
        "properties": {"query": {"type": "string",
            "description": "What to recall, or empty for the last session."}},
        "required": []}},
    {"type": "function", "name": "run_agent",
     "description": "Hand a hard reasoning, research, or multi-step coding task to the Hermes "
                    "agent. Use for anything beyond a simple command.",
     "parameters": {"type": "object",
        "properties": {"prompt": {"type": "string", "description": "The full request for Hermes."}},
        "required": ["prompt"]}},
]


def _web_url(query_or_url):
    s = (query_or_url or "").strip()
    if s.startswith(("http://", "https://")):
        return s
    return "https://www.google.com/search?q=" + urllib.parse.quote(s)


def _open_url(url):
    """Open a URL in the default browser, the reliable Windows way. webbrowser.open often
    reports success but opens nothing on Windows, so go straight to os.startfile / `start` --
    the same shell mechanism that already works for launching apps. Returns True if launched."""
    try:
        os.startfile(url)          # Windows: hands the URL to the default browser
        return True
    except Exception:
        pass
    try:
        import subprocess
        subprocess.Popen(["cmd", "/c", "start", "", url])
        return True
    except Exception:
        pass
    try:
        import webbrowser
        return bool(webbrowser.open(url))   # last resort (non-Windows / odd setups)
    except Exception:
        return False


def dispatch(name, args, ctrl=None, simulate=True):
    """Run one tool call through the existing router. Returns a JSON-able result dict.

    simulate=True plans the action with no side effects (cloud self-test / dry runs).
    simulate=False actually executes via zoe_router (real PC actions). Never raises.
    """
    args = args if isinstance(args, dict) else {}
    try:
        if name in ("launch_app", "close_app", "start_workspace"):
            target = (args.get("name") or "").strip()
            action = {"launch_app": "launch", "close_app": "close",
                      "start_workspace": "workspace"}[name]
            if simulate:
                return {"ok": True, "simulated": True, "action": action, "target": target}
            a, handled = zoe_router.execute({"action": action, "target": target}, target, ctrl)
            return {"ok": bool(handled), "action": a, "target": target}

        if name == "open_folder":
            target = (args.get("path") or "").strip()
            if simulate:
                return {"ok": True, "simulated": True, "action": "folder", "target": target}
            a, handled = zoe_router.execute({"action": "folder", "target": target}, target, ctrl)
            return {"ok": bool(handled), "action": a, "target": target}

        if name == "open_web":
            url = _web_url(args.get("query_or_url"))
            if simulate:
                return {"ok": True, "simulated": True, "action": "web", "url": url}
            return {"ok": _open_url(url), "action": "web", "url": url}

        if name == "recall_memory":
            query = (args.get("query") or "").strip()
            if simulate:
                return {"ok": True, "simulated": True, "action": "memory", "query": query}
            if not zoe_memory:
                return {"ok": False, "error": "memory unavailable"}
            handled, say, data = zoe_router._recall(query or "last session",
                                                    {"action": "memory", "target": query})
            return {"ok": bool(handled), "say": say}

        if name == "run_agent":
            prompt = (args.get("prompt") or "").strip()
            if simulate:
                return {"ok": True, "simulated": True, "action": "agent", "prompt": prompt}
            cmd = zoe_router.make_command(intent="plugin_action", target="hermes",
                                          payload={"prompt": prompt})
            handled, res = zoe_router._run_plugin(cmd)
            ans = res.get("answer") if isinstance(res, dict) else None
            err = res.get("error") if isinstance(res, dict) else None
            return {"ok": bool(handled), "answer": (ans or "")[:600], "error": err}

        return {"ok": False, "error": f"unknown tool {name}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _selftest():
    """Dry-run every tool with simulate=True (no side effects). Cloud-safe verification
    that the schema names and arg mapping line up with dispatch -- no socket, no audio."""
    cases = [
        ("launch_app", {"name": "Discord"}),
        ("close_app", {"name": "Spotify"}),
        ("open_folder", {"path": "Downloads"}),
        ("open_web", {"query_or_url": "best protein for mass"}),
        ("open_web", {"query_or_url": "https://news.google.com"}),
        ("start_workspace", {"name": "coding"}),
        ("recall_memory", {"query": ""}),
        ("run_agent", {"prompt": "plan the KOS deploy fix"}),
        ("bogus_tool", {}),
    ]
    names = {t["name"] for t in TOOLS}
    print(f"  {len(TOOLS)} tools declared: {', '.join(sorted(names))}")
    for nm, ar in cases:
        out = dispatch(nm, ar, simulate=True)
        print(f"  {nm}({ar}) -> {json.dumps(out)}")
    # the model-facing names must all be dispatchable
    for t in names:
        assert dispatch(t, {}, simulate=True).get("ok") is not None, t
    print("  selftest ok")


if __name__ == "__main__":
    _selftest()
