#!/usr/bin/env python3
"""Import Chris's research second-brain (C:\\Users\\chris\\Zoe) INTO JARVIS/Zoey's Obsidian
memory vault, so Zoey natively KNOWS it — recall by voice, the command bar, /memory search,
and the Obsidian browser. Everything lands in the vault's `research/` folder.

Idempotent: same title overwrites (no duplicates). Additive: never touches existing notes.
Best-effort. Run: python tools/zoe_import_research.py   [--no-transcripts]
"""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zoe_memory as m

ZOE = r"C:\Users\chris\Zoe"
BRAIN = os.path.join(ZOE, "Brain")
FOLDER = "research"


def _read(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""


def _put(title, content, tags):
    """Write one research note into the vault (frontmatter like zoe_memory.write, but no per-note
    index rebuild — we rebuild once at the end)."""
    if not (content or "").strip():
        return 0
    rel = os.path.join(FOLDER, m._slug(title) + ".md")
    fm = ["---", f"title: {title}", f"created: {m._now()}",
          "tags: [" + ", ".join(tags) + "]", "source: research-vault (C:/Users/chris/Zoe)", "---", ""]
    m._write(os.path.join(m.VAULT, rel), "\n".join(fm) + content.rstrip() + "\n")
    return 1


def main():
    transcripts = "--no-transcripts" not in sys.argv
    n = 0

    # 1) Curated knowledge — the distilled intelligence (synthesis, roadmap, ideas)
    for sub, tag in (("Maps of Content", "synthesis"),
                     ("Architecture Notes", "architecture"),
                     ("Future Ideas", "ideas")):
        for p in sorted(glob.glob(os.path.join(BRAIN, sub, "*.md"))):
            n += _put(os.path.basename(p)[:-3], _read(p), ["research", tag])

    # 2) Creator Intelligence digest (from the ranked DB)
    try:
        cr = json.load(open(os.path.join(ZOE, "Memory", "creators.json"), encoding="utf-8"))
        L = [f"# Creator Intelligence — {len(cr)} creators ranked by learning value\n",
             "| # | Creator | Platforms | Items | Niches | Learn | Conf |",
             "|---|---|---|---|---|---|---|"]
        for i, c in enumerate(cr, 1):
            L.append(f"| {i} | {c.get('name')} | {', '.join(c.get('platforms', []))} | "
                     f"{c.get('content_count')} | {', '.join(c.get('niches', []))} | "
                     f"{c.get('learning_value')} | {c.get('confidence')} |")
        n += _put("Creator Intelligence", "\n".join(L), ["research", "creators"])
    except Exception:
        pass

    # 3) Instagram Watchlist (the 55 resolved profiles)
    try:
        ig = json.load(open(os.path.join(ZOE, "Automation", "ig-creators.json"), encoding="utf-8"))
        L = [f"# Instagram Watchlist — {len(ig)} AI/automation creators Zoe watches\n"]
        for c in ig:
            h = (c.get("url") or "").rstrip("/").split("/")[-1]
            L.append(f"- [{c.get('name')}]({c.get('url')}) — @{h}")
        n += _put("Instagram Watchlist", "\n".join(L), ["research", "instagram"])
    except Exception:
        pass

    # 4) The raw corpus — every video/reel transcript (the searchable knowledge base)
    vr = 0
    if transcripts:
        for p in sorted(glob.glob(os.path.join(BRAIN, "Video Research", "*.md"))):
            if os.path.basename(p).startswith("_"):
                continue
            vr += _put(os.path.basename(p)[:-3], _read(p), ["research", "video"])
        n += vr

    m._build_index()
    print(f"imported {n} research notes into {m.VAULT}\\{FOLDER}  ({vr} video transcripts)")
    print("Zoey now knows them: ask the command bar 'what do I know about reels', or GET /memory/read?q=reels")


if __name__ == "__main__":
    main()
