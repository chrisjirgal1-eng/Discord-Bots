#!/usr/bin/env python3
"""Zoe's full self-diagnostic: tests every subsystem (voice + tools, API keys, wake-word STT, deps,
ecosystem OS, backend ports, memory, ops loop + self-coding, system) and reports whether she is fully
online. Lightweight; never raises.

  python tools/zoe_diag.py
"""
import os, sys, json, socket, subprocess, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def _env(key):
    v = os.environ.get(key)
    if v:
        return v
    try:
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def _port(p):
    try:
        s = socket.create_connection(("127.0.0.1", p), timeout=1.5)
        s.close()
        return True
    except Exception:
        return False


def _http(url, headers=None, timeout=8):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("Voice + tools")
def _c_tools():
    import zoe_tools
    n = len(zoe_tools.TOOLS)
    # a tool is truly broken only if it has NO dispatch handler; arg-validation errors are fine
    unwired = [t["name"] for t in zoe_tools.TOOLS
               if (zoe_tools.dispatch(t["name"], {}, simulate=True).get("error") or "").startswith("unknown tool")]
    return ("ok" if not unwired else "fail", f"{n} tools all wired" if not unwired else f"{n} tools, {len(unwired)} unwired")


@check("OpenAI key (voice + wake-word STT)")
def _c_openai():
    k = _env("OPENAI_API_KEY")
    if not k:
        return ("fail", "no key")
    code = _http("https://api.openai.com/v1/models", {"Authorization": "Bearer " + k})
    return ("ok" if code == 200 else "fail", f"auth HTTP {code}")


@check("Speech deps (pyautogui, Pillow, psutil)")
def _c_deps():
    missing = [m for m in ("pyautogui", "PIL", "psutil") if not _try_import(m)]
    return ("ok" if not missing else "warn", "all present" if not missing else "missing: " + ", ".join(missing))


def _try_import(m):
    try:
        __import__(m)
        return True
    except Exception:
        return False


@check("Ecosystem OS registry")
def _c_eco():
    p = Path(r"C:\Users\chris\Zoe\os\registry.json")
    if not p.exists():
        return ("warn", "registry not built (run build_registry.py)")
    try:
        return ("ok", f"{json.loads(p.read_text(encoding='utf-8')).get('count', 0)} capabilities indexed")
    except Exception as e:
        return ("warn", str(e)[:60])


@check("Backend servers (7717 / 7766)")
def _c_ports():
    t, c = _port(7717), _port(7766)
    if t and c:
        return ("ok", "telemetry + control up")
    if t or c:
        return ("warn", f"telemetry {'up' if t else 'down'}, control {'up' if c else 'down'}")
    return ("warn", "not running (open the app)")


@check("Memory vault")
def _c_mem():
    try:
        import zoe_memory
        zoe_memory.read()
        return ("ok", "vault readable")
    except Exception as e:
        return ("warn", str(e)[:60])


@check("Ops loop + self-coding")
def _c_ops():
    try:
        import zoe_ops_loop
        cfg = zoe_ops_loop.load_cfg()
        try:
            cl = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=15)
            claude = "claude ready" if cl.returncode == 0 else "claude not available"
        except Exception:
            claude = "claude not on PATH"
        return ("ok", f"actor={cfg.get('actor')}, evolve={cfg.get('evolve')}, {claude}")
    except Exception as e:
        return ("warn", str(e)[:60])


@check("System")
def _c_sys():
    try:
        import psutil
        return ("ok", f"CPU {int(psutil.cpu_percent(0.2))}%, memory {int(psutil.virtual_memory().percent)}%")
    except Exception:
        return ("warn", "psutil unavailable")


def run():
    results = []
    for name, fn in CHECKS:
        try:
            st, detail = fn()
        except Exception as e:
            st, detail = "warn", str(e)[:60]
        results.append({"name": name, "status": st, "detail": detail})
    fails = [r for r in results if r["status"] == "fail"]
    warns = [r for r in results if r["status"] == "warn"]
    green = len(results) - len(fails) - len(warns)
    if not fails and not warns:
        say = f"All systems online and fully running, sir. {len(results)} of {len(results)} checks green."
    elif not fails:
        say = (f"Systems online, sir, {green} of {len(results)} green. Minor notes: "
               + "; ".join(f"{r['name']} ({r['detail']})" for r in warns[:3]) + ".")
    else:
        say = ("Heads up, sir, something needs attention: "
               + "; ".join(f"{r['name']} {r['detail']}" for r in fails[:3])
               + f". {green} of {len(results)} green.")
    return {"ok": not fails, "all_ok": not fails and not warns, "checks": results, "say": say}


if __name__ == "__main__":
    r = run()
    for c in r["checks"]:
        print(f"  [{c['status'].upper():4}] {c['name']:36} {c['detail']}")
    print("\n" + r["say"])
