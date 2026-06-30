#!/usr/bin/env python3
"""JARVIS-owned research runner — runs the merged research engine (in ./research) on demand.

Default = REFRESH (rebuild creator rankings, discovery, trends, semantic index, capability
inventory, and the daily check-up) — fast, no network. Idempotent.
--full  = the whole daily cycle, including pulling NEW YouTube + Instagram content.

This is what makes JARVIS *own* the engine: she runs it herself, against her own data in
research/, with no dependency on the old C:\\Users\\chris\\Zoe folder. Run: python tools/run_research.py
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "research")
AUTO = os.path.join(RES, "Automation")
SEM = os.path.join(RES, "Memory", "semantic")


def _run(cmd):
    print(">>", " ".join(os.path.basename(c) for c in cmd), flush=True)
    try:
        return subprocess.run(cmd, timeout=900).returncode
    except Exception as e:
        print("   (skipped:", e, ")")
        return 1


def main():
    if not os.path.isdir(RES):
        print("research/ not found — the engine isn't merged in yet."); return 1
    if "--full" in sys.argv:
        print("running the FULL daily cycle (pulls new videos/reels)…")
        return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                               "-File", os.path.join(AUTO, "zoe-cycle.ps1")]).returncode
    # refresh: the offline processing half — fast, no network, no ban risk
    for s in ("build-creators.py", "discover-creators.py", "trends.py", "capabilities.py", "checkup.py"):
        _run([sys.executable, os.path.join(AUTO, s)])
    _run(["node", os.path.join(SEM, "build-index.mjs")])
    print("\nresearch refreshed (in ./research). Run with --full to also pull new content.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
