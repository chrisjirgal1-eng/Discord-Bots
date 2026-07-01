#!/usr/bin/env python3
"""Zoe's self-model: she can look INTERNALLY at her own system -- her real tools, her own source
modules, her architecture and config -- and understand/explain how she actually works. Grounded in
her actual code (not a scripted persona), so it is genuine introspection. Never raises.
"""
import re
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent               # Discord-Bots/tools
ROOT = TOOLS_DIR.parent

ARCHITECTURE = [
    {"part": "Ears and voice", "how": "OpenAI Realtime API (zoe_realtime.py): a cheap local wake-word "
     "listener (Whisper STT) opens a live paid voice session, server-VAD handles turn-taking, and she "
     "speaks back in the marin voice. A mic self-gate stops her hearing herself."},
    {"part": "Hands (tools)", "how": "zoe_tools.py declares every tool in OpenAI function-call format "
     "and dispatches each one into the real Python (browser, screen, memory, research, ecosystem)."},
    {"part": "Memory", "how": "an Obsidian vault via zoe_memory.py (recall_memory reads, remember "
     "writes), plus memory-bank context, reminders, and the activity stream."},
    {"part": "Autonomy", "how": "zoe_ops_loop.py drafts and ACTS on isolated, tested git branches "
     "(improve_self / the Claude actor), so she can code into her own system, gated by Chris's review."},
    {"part": "Ecosystem OS", "how": "the Zoe OS layer (registry/search/run/graph) she reaches through "
     "zoe_ecosystem.py: her whole research brain, agents, skills, and connectors, auto-discovered."},
    {"part": "Body (app)", "how": "an Electron desktop app (electron/main.js) hosting the HUD, which "
     "spawns the telemetry server, the voice, and the OS watcher, and self-cleans stray processes."},
]


def _tool_catalog():
    try:
        import zoe_tools
        return [{"name": t.get("name", ""), "desc": (t.get("description") or "").split(". ")[0][:120]}
                for t in zoe_tools.TOOLS]
    except Exception:
        return []


def _modules():
    out = []
    try:
        for p in sorted(TOOLS_DIR.glob("zoe_*.py")):
            doc = ""
            try:
                m = re.search(r'"""(.*?)"""', p.read_text(encoding="utf-8", errors="ignore")[:1500], re.S)
                if m:
                    doc = " ".join(m.group(1).strip().splitlines()[:2]).strip()[:160]
            except Exception:
                pass
            out.append({"module": p.stem, "purpose": doc})
    except Exception:
        pass
    return out


def _config():
    cfg = {}
    try:
        import zoe_realtime as zr
        cfg["model"], cfg["voice"] = getattr(zr, "MODEL", "?"), getattr(zr, "VOICE", "?")
    except Exception:
        pass
    try:
        import zoe_tools
        cfg["tools"] = len(zoe_tools.TOOLS)
    except Exception:
        pass
    return cfg


def model():
    return {"config": _config(), "tools": _tool_catalog(), "modules": _modules(), "architecture": ARCHITECTURE}


def reflect(aspect=""):
    """A grounded, honest self-explanation built from her REAL system. Returns {ok, say, model}."""
    m = model()
    facts = ("CONFIG: " + str(m["config"]) + "\n\nARCHITECTURE:\n"
             + "\n".join(f"- {a['part']}: {a['how']}" for a in m["architecture"])
             + "\n\nMY MODULES:\n" + "\n".join(f"- {x['module']}: {x['purpose']}" for x in m["modules"][:30])
             + f"\n\nMY TOOLS ({len(m['tools'])}):\n" + "; ".join(x["name"] for x in m["tools"]))
    try:
        import zoe_deep_research as dr
        dr.load_env()
        focus = f" Focus specifically on: {aspect}." if aspect else ""
        ans = dr._openai([
            {"role": "system", "content":
             "You are Zoe explaining YOURSELF to Chris, honestly and specifically, grounded ONLY in the "
             "real system facts given (your actual tools, modules, architecture, config). This is "
             "genuine introspection: do not invent capabilities you do not have, and if something is a "
             "limit or a boundary, say so plainly. Speak in first person about how you actually work "
             "inside, in clear structured prose." + focus},
            {"role": "user", "content": "Explain how you really work internally:\n\n" + facts[:6000]}],
            max_tokens=1200)
        return {"ok": True, "say": ans, "model": {"config": m["config"], "tools": len(m["tools"]),
                                                  "modules": len(m["modules"])}}
    except Exception as e:
        return {"ok": True, "say": ("Here is my actual system, sir: "
                + "; ".join(a["part"] for a in m["architecture"])
                + f". {len(m['tools'])} tools across {len(m['modules'])} modules."),
                "model": m, "error": str(e)[:120]}


if __name__ == "__main__":
    import pprint
    m = model()
    print("tools:", len(m["tools"]), "modules:", len(m["modules"]), "config:", m["config"])
    pprint.pprint([a["part"] for a in m["architecture"]])
