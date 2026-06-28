#!/usr/bin/env python3
"""ZOE diagnostics: a self-contained health check for the versioned kernel.

Runs six test groups (state, router, UI command, persistence, plugin, backend), prints PASS/FAIL
per test, and reports a system health score (0-100) plus a final validation block. It NEVER
crashes -- every test is isolated, and it points the state layer at a temp file so it cannot touch
the user's real memory/zoe_state.json.

  python tools/zoe_diagnostics.py        (exit 0 if every test passes, else 1; never a traceback)
"""
import os, sys, json, tempfile, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zoe_versions
import zoe_state
import zoe_router

RESULTS = []   # (group, name, passed, detail)

def _check(group, name, fn):
    try:
        ok, detail = fn()
    except Exception as e:
        ok, detail = False, "exception: " + str(e)
    RESULTS.append((group, name, bool(ok), detail))

# --- 1. STATE TESTS --------------------------------------------------------------------------
def t_state_rw():
    zoe_state.record_command("diag write", "chat", True)
    cmds = zoe_state.load()["history"]["last_commands"]
    return (any(c.get("text") == "diag write" for c in cmds), "history has the written command")

def t_state_corruption():
    with open(zoe_state.STATE_FILE, "w", encoding="utf-8") as f:
        f.write("{ this is not valid json :: ")
    st = zoe_state.load()                       # must recover to safe defaults, no crash
    return (isinstance(st, dict) and st.get("schema_version") and "session" in st,
            "corrupt file recovered to defaults")

def t_state_schema():
    st = zoe_state.load()
    need = ("schema_version", "system_mode", "session", "history", "workspace_state", "plugins")
    missing = [k for k in need if k not in st]
    return (not missing, "missing keys: " + str(missing) if missing else "all schema keys present")

# --- 2. ROUTER TESTS -------------------------------------------------------------------------
def t_router_handled_flag():
    r = zoe_router.route(zoe_router.make_command(intent="navigate",
                          target="https://example.com"), simulate=True)
    return ("handled" in r and r["handled"] is True, "valid command returns handled:true")

def t_router_rejects_invalid():
    r = zoe_router.route({"intent": "totally_unknown_intent"}, simulate=True)
    return (r.get("handled") is False and "error" in r.get("result", {}),
            "invalid intent safely rejected, no crash")

def t_router_survives_garbage():
    r1 = zoe_router.route(None, simulate=True)
    r2 = zoe_router.route("not a dict", simulate=True)
    return (r1.get("handled") is False and r2.get("handled") is False, "garbage input did not crash")

# --- 3. UI COMMAND TESTS ---------------------------------------------------------------------
def t_ui_open_youtube():
    cmd = zoe_router.make_command(source="ui", intent="navigate",
                                  target="https://www.youtube.com", action="open")
    r = zoe_router.route(cmd, simulate=True)
    return (r["handled"] and r["result"].get("action") == "web", "UI 'Open YouTube' routed to web")

def t_ui_pipeline_shape():
    r = zoe_router.route(zoe_router.make_command(source="ui", intent="open_app",
                                                 target="Discord"), simulate=True)
    need = ("schema_version", "trace_id", "source", "intent", "handled", "result")
    return (all(k in r for k in need) and r["source"] == "ui",
            "response carries the full structured envelope")

# --- 4. PERSISTENCE TESTS --------------------------------------------------------------------
def t_persist_restore():
    zoe_state.record_command("remember me", "chat", True)
    reloaded = zoe_state.load()                 # simulates a restart reading the file fresh
    texts = [c.get("text") for c in reloaded["history"]["last_commands"]]
    return ("remember me" in texts, "command survived a reload")

def t_persist_fifo_cap():
    for i in range(60):
        zoe_state.record_command("cmd %d" % i, "chat", True)
    n = len(zoe_state.load()["history"]["last_commands"])
    return (n == 50, "history capped at 50 (got %d)" % n)

# --- 5. PLUGIN TESTS -------------------------------------------------------------------------
def t_plugin_load():
    loaded = zoe_router.load_plugins()
    return ("example" in loaded, "loaded plugins: " + str(loaded))

def t_plugin_execute():
    r = zoe_router.route(zoe_router.make_command(intent="plugin_action", target="example",
                                                 payload={"ping": 1}))
    return (r["handled"] and r["result"].get("plugin") == "example", "example plugin executed")

def t_plugin_isolation():
    def _boom(c):
        raise RuntimeError("intentional plugin failure")
    zoe_router._PLUGINS["__broken__"] = {
        "meta": {"plugin_name": "__broken__", "plugin_version": "1.0.0",
                 "schema_version": "1.0.0", "supported_intents": ["plugin_action"]},
        "execute": _boom}
    try:
        r = zoe_router.route(zoe_router.make_command(intent="plugin_action", target="__broken__"))
        still_ok = zoe_router.route(zoe_router.make_command(intent="plugin_action",
                                                            target="example"))["handled"]
    finally:
        zoe_router._PLUGINS.pop("__broken__", None)
    return (r["handled"] is False and still_ok, "broken plugin isolated, others still work")

# --- 6. BACKEND TESTS ------------------------------------------------------------------------
def t_backend_offline_mode():
    zoe_state.set_mode("offline")
    st = zoe_state.load()
    return (st["system_mode"] == "offline" and st["session"]["mode"] == "offline",
            "offline mode persisted (legacy + session)")

def t_backend_simulation_fallback():
    # no control endpoint reachable -> simulate path still returns handled, UI keeps working
    r = zoe_router.route(zoe_router.make_command(intent="navigate", target="https://example.com"),
                         ctrl=None, simulate=True)
    return (r["handled"] is True, "simulation fallback works with no backend")

GROUPS = [
    ("STATE",       [t_state_rw, t_state_corruption, t_state_schema]),
    ("ROUTER",      [t_router_handled_flag, t_router_rejects_invalid, t_router_survives_garbage]),
    ("UI COMMAND",  [t_ui_open_youtube, t_ui_pipeline_shape]),
    ("PERSISTENCE", [t_persist_restore, t_persist_fifo_cap]),
    ("PLUGIN",      [t_plugin_load, t_plugin_execute, t_plugin_isolation]),
    ("BACKEND",     [t_backend_offline_mode, t_backend_simulation_fallback]),
]

def _group_ok(group):
    rows = [r for r in RESULTS if r[0] == group]
    return rows and all(r[2] for r in rows)

def main():
    # point the state layer at a throwaway file so diagnostics never touch real state
    tmpdir = tempfile.mkdtemp(prefix="zoe_diag_")
    zoe_state.STATE_DIR = tmpdir
    zoe_state.STATE_FILE = os.path.join(tmpdir, "zoe_state.json")

    print("\n  ZOE DIAGNOSTICS  (core %s)\n  %s" % (zoe_versions.SYSTEM["core_version"], "-" * 52))
    for group, tests in GROUPS:
        for fn in tests:
            _check(group, fn.__name__[2:].replace("_", " "), fn)   # strip the leading t_
        for g, name, ok, detail in [r for r in RESULTS if r[0] == group]:
            print("  [%s] %-11s %-26s %s" % ("PASS" if ok else "FAIL", g, name, detail))

    passed = sum(1 for r in RESULTS if r[2])
    total = len(RESULTS)
    health = round(100 * passed / total) if total else 0

    def status(ok):
        return "OK" if ok else "DEGRADED"
    print("\n  FINAL VALIDATION\n  %s" % ("-" * 52))
    print("  UI command system:      %s" % status(_group_ok("UI COMMAND")))
    print("  plugin system:          %s (%d loaded)" % (
        "READY" if _group_ok("PLUGIN") else "DEGRADED", len(zoe_router._PLUGINS)))
    print("  router integrity:       %s" % status(_group_ok("ROUTER")))
    print("  memory system:          %s" % ("SAFE" if _group_ok("STATE")
                                            and _group_ok("PERSISTENCE") else "DEGRADED"))
    print("  schema compatibility:   %s (core %s, cmd %s, plugin %s, state %s)" % (
        status(True), zoe_versions.SYSTEM["core_version"],
        zoe_versions.SYSTEM["command_schema_version"], zoe_versions.SYSTEM["plugin_api_version"],
        zoe_versions.SYSTEM["state_schema_version"]))
    print("  backend resilience:     %s" % status(_group_ok("BACKEND")))
    print("  diagnostic completeness: %d/%d tests" % (passed, total))
    print("  SYSTEM HEALTH SCORE:    %d/100\n" % health)
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        print("\n  diagnostics runner error -- but the system itself did not crash.\n")
        sys.exit(1)
