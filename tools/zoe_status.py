#!/usr/bin/env python3
"""ZOE status generator: scans the repo and writes zoe-ui/config.json.

Run this after any structural change (new skill, plugin, test) to keep the HUD
counts accurate.  The server serves /config from the generated file.

    python tools/zoe_status.py          # write config.json and print summary
    python tools/zoe_status.py --json   # print JSON only, no file write
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _count_dir(rel, *, suffix=None, is_dir=False):
    path = os.path.join(ROOT, rel)
    if not os.path.isdir(path):
        return 0
    items = os.listdir(path)
    if is_dir:
        return sum(1 for i in items if os.path.isdir(os.path.join(path, i)))
    if suffix:
        return sum(1 for i in items if i.endswith(suffix) and not i.startswith("_"))
    return len(items)

def _test_count():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--co", "--tb=no"],
            capture_output=True, text=True, cwd=ROOT, timeout=30
        )
        return sum(1 for l in r.stdout.splitlines() if "::" in l)
    except Exception:
        return 0

def _git_head():
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, stderr=subprocess.DEVNULL, timeout=5
        ).decode().strip()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT, stderr=subprocess.DEVNULL, timeout=5
        ).decode().strip()
        return sha, branch
    except Exception:
        return "unknown", "unknown"

def build():
    sha, branch = _git_head()

    skills  = _count_dir(".claude/skills", is_dir=True)
    plugins = max(0, _count_dir("plugins", suffix=".py") - 2)  # exclude example + __init__
    tools   = _count_dir("tools", suffix=".py")
    tests   = _test_count()

    # agent files: count VoltAgent installed agent .md files in Claude's user scope
    agent_paths = [
        os.path.expandvars(r"%APPDATA%\Claude\agents"),
        os.path.expanduser("~/.claude/agents"),
    ]
    agents = 0
    for p in agent_paths:
        if os.path.isdir(p):
            agents = sum(1 for f in os.listdir(p) if f.endswith(".md"))
            if agents:
                break

    return {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "branch": branch,
        "head": sha,
        "skills": skills,
        "tests": tests,
        "plugins": plugins,
        "tools": tools,
        "agents": agents,
    }

def main():
    cfg = build()
    json_only = "--json" in sys.argv
    if not json_only:
        out = os.path.join(ROOT, "zoe-ui", "config.json")
        with open(out, "w") as f:
            json.dump(cfg, f, indent=2)
        print(f"Written -> {out}")
        print(f"  skills={cfg['skills']}  tests={cfg['tests']}  plugins={cfg['plugins']}  tools={cfg['tools']}  agents={cfg['agents']}")
        print(f"  branch={cfg['branch']}  head={cfg['head']}")
    else:
        print(json.dumps(cfg, indent=2))

if __name__ == "__main__":
    main()
