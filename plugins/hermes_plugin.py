#!/usr/bin/env python3
"""Hermes connector: hand a request to the locally-installed Nous Research Hermes agent.

Wires Hermes (hermes-agent.nousresearch.com) into Zoe through the plugin system. A plugin_action
targeting "hermes" runs `hermes -z "<prompt>"` (oneshot mode: prompt in, final answer out) on the
installed hermes executable and returns the answer. Additive -- no router core changes.

Hermes must be installed (%LOCALAPPDATA%\\hermes) AND have a model configured (`hermes setup` /
`hermes model`) to actually answer; until then this returns a clean, explanatory error.
"""
import os, glob, shutil, subprocess

PLUGIN = {
    "plugin_name": "hermes",
    "plugin_version": "1.0.0",
    "schema_version": "1.0.0",
    "supported_intents": ["plugin_action"],
}

def _hermes_exe():
    """Resolve the hermes executable. Order: HERMES_EXE (full path) -> PATH -> HERMES_HOME ->
    %LOCALAPPDATA%\\hermes, each checking the known venv layout then a recursive search. Set
    HERMES_EXE or HERMES_HOME in Zoe's .env if Hermes lives somewhere non-standard."""
    direct_env = os.environ.get("HERMES_EXE")
    if direct_env and os.path.exists(direct_env):
        return direct_env
    p = shutil.which("hermes")
    if p:
        return p
    bases = []
    if os.environ.get("HERMES_HOME"):
        bases.append(os.environ["HERMES_HOME"])
    if os.environ.get("LOCALAPPDATA"):
        bases.append(os.path.join(os.environ["LOCALAPPDATA"], "hermes"))
    for base in bases:
        direct = os.path.join(base, "hermes-agent", "venv", "Scripts", "hermes.exe")
        if os.path.exists(direct):
            return direct
        hits = (glob.glob(os.path.join(base, "**", "hermes.exe"), recursive=True)
                or glob.glob(os.path.join(base, "**", "hermes"), recursive=True))
        if hits:
            return hits[0]
    return None

def execute(command):
    command = command or {}
    payload = command.get("payload") or {}
    prompt = (payload.get("prompt") or payload.get("text") or command.get("target") or "").strip()
    if not prompt:
        return {"handled": False, "result": {"error": "no prompt for Hermes"}}
    exe = _hermes_exe()
    if not exe:
        return {"handled": False, "result": {
            "error": "Hermes is not installed yet. Run the Nous installer, then `hermes setup`."}}
    try:
        r = subprocess.run([exe, "-z", prompt], capture_output=True, text=True, timeout=180,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        answer = (r.stdout or "").strip() or (r.stderr or "").strip()
        ok = (r.returncode == 0 and bool(r.stdout.strip()))
        return {"handled": ok, "result": {
            "agent": "hermes", "prompt": prompt, "answer": answer[:4000],
            "code": r.returncode,
            "error": None if ok else "Hermes returned no answer (configure a model: `hermes model`)."}}
    except subprocess.TimeoutExpired:
        return {"handled": False, "result": {"error": "Hermes timed out (180s)."}}
    except Exception as e:
        return {"handled": False, "result": {"error": str(e)}}
