#!/usr/bin/env python3
"""Zoe's self-progression: she can see and speak about her own growth -- what's been added, how many
capabilities she has now, and how far she's come. Reads her own git history (the real changelog) plus
the ecosystem registry, and keeps dated snapshots so she can recognize what's new. Never raises.
"""
import os, json, subprocess, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                       # Discord-Bots
OS_REG = Path(r"C:\Users\chris\Zoe\os\registry.json")
SNAP = ROOT / "memory" / "progression.jsonl"


def _git(args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True,
                              timeout=20).stdout.strip()
    except Exception:
        return ""


def changelog(n=14):
    """Her real feature history = her commits. [{subject, when}] newest first."""
    rows = []
    for line in _git(["log", f"-{n}", "--no-merges", "--pretty=%s\t%cr"]).splitlines():
        if "\t" in line:
            subj, when = line.split("\t", 1)
            rows.append({"subject": subj.strip(), "when": when.strip()})
    return rows


def _registry_count():
    try:
        return json.loads(OS_REG.read_text(encoding="utf-8")).get("count", 0)
    except Exception:
        return 0


def _snapshots():
    try:
        return [json.loads(l) for l in SNAP.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []


def stats(tool_count=None):
    return {"date": datetime.date.today().isoformat(), "tools": tool_count,
            "resources": _registry_count(), "commits": int(_git(["rev-list", "--count", "HEAD"]) or 0)}


def snapshot(tool_count=None):
    """Record today's stats once per day so growth is measurable over time."""
    try:
        s = stats(tool_count)
        prev = _snapshots()
        if prev and prev[-1].get("date") == s["date"]:
            return s
        os.makedirs(SNAP.parent, exist_ok=True)
        with open(SNAP, "a", encoding="utf-8") as f:
            f.write(json.dumps(s) + "\n")
        return s
    except Exception:
        return {}


def summary(tool_count=None):
    snapshot(tool_count)
    log = changelog(10)
    snaps = _snapshots()
    res = _registry_count()
    first = snaps[0] if snaps else None
    parts = []
    if tool_count:
        parts.append(f"I'm at {tool_count} voice tools now")
    if res:
        parts.append(f"and {res} capabilities indexed across the whole ecosystem")
    grew = ""
    if first and tool_count and first.get("tools") and first["tools"] < tool_count:
        grew = f" I've grown from {first['tools']} tools to {tool_count} since {first['date']}."
    recent = "; ".join(c["subject"] for c in log[:4])
    say = ("Quite a journey, sir. " + ", ".join(parts) + "." + grew
           + (f" Lately I added: {recent}." if recent else "")).strip()
    return {"ok": True, "tools": tool_count, "resources": res,
            "recent": [c["subject"] for c in log[:8]], "since": (first or {}).get("date"), "say": say}


if __name__ == "__main__":
    import pprint
    pprint.pprint(summary(50))
