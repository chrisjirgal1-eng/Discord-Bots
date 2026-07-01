#!/usr/bin/env python3
"""Bridge from Zoey's voice to the Zoe OS ecosystem (C:\\Users\\chris\\Zoe\\os): universal search,
run any resource, browse the registry, and explain what's happening. Calls the os/ scripts as
subprocesses for clean isolation; reads registry.json / activity.jsonl directly. Never raises.
"""
import sys, json, subprocess
from pathlib import Path

OS_DIR = Path(r"C:\Users\chris\Zoe\os")
PY = sys.executable
REG = OS_DIR / "registry.json"
ACT = OS_DIR / "activity.jsonl"


def _call(script, *args, timeout=120):
    try:
        cp = subprocess.run([PY, str(OS_DIR / script), *map(str, args)],
                            capture_output=True, text=True, timeout=timeout, cwd=str(OS_DIR.parent))
        for line in reversed((cp.stdout or "").strip().splitlines()):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        return {"ok": False, "error": (cp.stderr or "no output")[:200]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def search(query):
    return _call("search.py", query, "--json")


def run(resource, args="", dry=False):
    a = [resource, "--json"]
    if args:
        a += ["--args", args]
    if dry:
        a += ["--dry"]
    return _call("run.py", *a, timeout=600)


def list_resources(category=""):
    try:
        reg = json.loads(REG.read_text(encoding="utf-8"))
        recs = reg.get("resources", [])
        if category:
            c = category.lower().rstrip("s")
            recs = [r for r in recs if c in r["category"].lower()]
        items = [{"name": r["name"], "category": r["category"],
                  "use": r.get("launch_command") or r.get("description", "")[:60]} for r in recs]
        return {"ok": True, "count": len(items), "by_category": reg.get("by_category", {}), "items": items[:40]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def explain():
    try:
        evs = []
        if ACT.exists():
            for ln in ACT.read_text(encoding="utf-8").splitlines()[-6:]:
                try:
                    evs.append(json.loads(ln))
                except Exception:
                    pass
        evs = list(reversed(evs))
        recent = [f"{e.get('resource', '')} {e.get('phase', '')} ({e.get('status', '')})" for e in evs]
        cur = ""
        if evs:
            e0 = evs[0]
            cur = f"{e0.get('resource', '')} {e0.get('phase', '')}: {e0.get('detail', '')}".strip()
        n = 0
        try:
            n = json.loads(REG.read_text(encoding="utf-8")).get("count", 0)
        except Exception:
            pass
        if not recent:
            return {"ok": True, "idle": True,
                    "say": f"Idle and standing by, sir. I've got {n} capabilities indexed across the ecosystem."}
        say = (f"Right now I'm on {cur}." if cur else "Working through the ecosystem.")
        if len(recent) > 1:
            say += " Just before that: " + "; ".join(recent[1:4]) + "."
        say += f" {n} capabilities indexed in all."
        return {"ok": True, "current": cur, "recent": recent, "say": say}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


if __name__ == "__main__":
    import pprint
    pprint.pprint(explain())
    pprint.pprint({k: v for k, v in list_resources("agent").items() if k != "items"})
