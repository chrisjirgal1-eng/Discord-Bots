#!/usr/bin/env python3
"""Bridge to Chris's research second-brain at C:\\Users\\chris\\Zoe (a SEPARATE system from
this desktop app). Read-only views for the HUD's Research Lab page: the agent pipeline,
capability inventory, ranked creators, the Instagram watch-list, and semantic vault search.

Pure stdlib + the research repo's own `search.mjs` (node). Best-effort: every call returns a
safe default on error so the telemetry server never breaks because the other repo moved.
"""
import json, os, subprocess, collections
from pathlib import Path

# JARVIS now OWNS the research engine: it lives in Discord-Bots/research (merged in, no longer
# a bridge to an external folder). Falls back to the old location only if the merge dir is absent.
_MERGED = Path(__file__).resolve().parents[1] / "research"
ZOE = _MERGED if _MERGED.exists() else Path(r"C:\Users\chris\Zoe")
SEM = ZOE / "Memory" / "semantic"

AGENT_ROLES = {
    "feed-watcher":  "Research Feed — polls creator channels for new uploads",
    "indexer":       "Semantic Index — embeds the vault for meaning search",
    "synthesist":    "Synthesist — cross-reel insight synthesis",
    "creator-intel": "Creator Intelligence — ranks creators by learning value",
    "discovery":     "Creator Discovery — mines the vault for new creators",
    "trends":        "Trend Analyst — what's rising across recent notes",
    "ig-feed":       "Instagram Feed — polls IG profiles via the cookie file",
    "tiktok-feed":   "TikTok Feed — polls TikTok profiles for new videos (no auth)",
    "twitter-pull":  "Twitter/X Puller — pulls queued tweet videos (manual queue)",
    "ig-cookies":    "IG Cookie Export — refreshes the Instagram login",
    "ig-resolve":    "IG Profile Resolver — saved reels -> profile URLs",
    "pull-queue":    "IG Backfill — batch-pulls queued reels",
    "capabilities":  "Capability Inventory — probes tools, APIs, models",
    "checkup":       "Daily Check-up — health gate",
}


def _load(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def agents():
    """Group Logs/agents.jsonl into per-agent cards (same shape as the research dashboard)."""
    events = collections.defaultdict(list)
    try:
        for ln in (ZOE / "Logs" / "agents.jsonl").read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                e = json.loads(ln)
            except Exception:
                continue
            events[e.get("agent") or "unknown"].append(e)
    except FileNotFoundError:
        pass
    names = list(AGENT_ROLES.keys()) + [a for a in events if a not in AGENT_ROLES]
    out = []
    for name in names:
        evs = events.get(name, [])
        last = evs[-1] if evs else None
        files = []
        for e in evs:
            f = (e.get("file") or "").strip()
            if f and f not in files:
                files.append(f)
        out.append({
            "name": name,
            "role": AGENT_ROLES.get(name, "agent"),
            "status": last.get("status") if last else "idle",
            "last_task": (last.get("task") if last else "") or "—",
            "last_update": last.get("ts") if last else None,
            "files_touched": files[-5:],
            "event_count": len(evs),
        })
    return out


def capabilities():
    return _load(ZOE / "Memory" / "capabilities.json", {"empty": True, "hint": "run capabilities.py"})


def creators():
    d = _load(ZOE / "Memory" / "creators.json", [])
    return d if isinstance(d, list) else []


def watchlist():
    d = _load(ZOE / "Automation" / "ig-creators.json", [])
    return d if isinstance(d, list) else []


def search(q):
    if not q:
        return []
    try:
        r = subprocess.run(["node", str(SEM / "search.mjs"), q], capture_output=True, text=True,
                           env=dict(os.environ, ZOE_JSON="1"), timeout=60)
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"error": str(e)}


def summary():
    """One-glance counts for the lab header."""
    caps = capabilities()
    return {
        "agents": len(agents()),
        "creators": len(creators()),
        "watchlist": len(watchlist()),
        "capabilities": (caps.get("counts", {}) or {}).get("total", 0) if isinstance(caps, dict) else 0,
        "healthy": ((caps.get("counts", {}) or {}).get("by_health", {}) or {}).get("ok", 0) if isinstance(caps, dict) else 0,
    }


def voice():
    """Voice Intelligence dashboard data: engine capabilities, recent latency/turn metrics,
    learned-route count, and the custom-vocab keyterms. Best-effort (JARVIS-local data)."""
    out = {"capabilities": {}, "keyterms": [], "learned_routes": 0,
           "metrics": {"turns": 0, "avg_reply_ms": None, "recent": []}}
    try:
        import zoe_voice
        out["capabilities"] = zoe_voice.capabilities()
        out["keyterms"] = zoe_voice.keyterms()
    except Exception:
        pass
    try:
        import zoe_learn
        out["learned_routes"] = len(zoe_learn.all() or {})
    except Exception:
        pass
    mp = Path(__file__).resolve().parents[1] / "memory" / "voice_metrics.jsonl"
    turns, lat = [], []
    try:
        for ln in mp.read_text(encoding="utf-8").splitlines()[-300:]:
            try:
                e = json.loads(ln)
            except Exception:
                continue
            if e.get("event") == "turn":
                turns.append(e)
                if e.get("reply_ms"):
                    lat.append(e["reply_ms"])
    except Exception:
        pass
    out["metrics"] = {"turns": len(turns),
                      "avg_reply_ms": round(sum(lat) / len(lat)) if lat else None,
                      "recent": turns[-8:]}
    return out
