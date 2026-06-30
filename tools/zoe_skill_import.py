#!/usr/bin/env python3
"""Import a skill (its SKILL.md playbook) from a public GitHub repo into Zoe's .claude/skills, so
use_skill can run it. Inspired by OpenJarvis skill import. SAFE: only the markdown playbook is
downloaded -- no scripts are fetched or executed -- so importing a skill just adds instructions.

  python tools/zoe_skill_import.py owner/repo skill-name
  python tools/zoe_skill_import.py https://github.com/owner/repo/blob/main/skills/foo/SKILL.md foo
"""
import os, sys, re, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, ".claude", "skills")
UA = "Mozilla/5.0 (zoe-skill-import)"


def _get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            if getattr(r, "status", 200) == 200:
                return r.read().decode("utf-8", "replace")
    except Exception:
        pass
    return None


def _slug(s):
    return re.sub(r"[^a-z0-9-]+", "-", (s or "").lower()).strip("-") or "imported-skill"


def _candidates(source, skill):
    """Raw URLs to try for the SKILL.md, most specific first."""
    s = (source or "").strip()
    if "raw.githubusercontent.com" in s and s.endswith(".md"):
        return [s]
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", s)   # blob url -> raw
    if m:
        o, rp, br, path = m.groups()
        return ["https://raw.githubusercontent.com/%s/%s/%s/%s" % (o, rp, br, path)]
    m = re.match(r"^([^/\s]+)/([^/\s]+)$", s)                                    # owner/repo (+ skill)
    if m and skill:
        o, rp = m.groups()
        sk = skill.strip().strip("/")
        urls = []
        for br in ("main", "master"):
            for path in ("skills/%s/SKILL.md" % sk, "%s/SKILL.md" % sk,
                         ".claude/skills/%s/SKILL.md" % sk, "src/skills/%s/SKILL.md" % sk):
                urls.append("https://raw.githubusercontent.com/%s/%s/%s/%s" % (o, rp, br, path))
        return urls
    return []


def import_skill(source, skill=None):
    """Fetch a skill's SKILL.md and install it under .claude/skills. Returns {ok, name, path, bytes}."""
    for url in _candidates(source, skill):
        body = _get(url)
        if body and len(body.strip()) > 20:
            name = _slug(skill or os.path.basename(os.path.dirname(url)))
            d = os.path.join(SKILLS, name)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(body)
            return {"ok": True, "name": name, "path": ".claude/skills/%s/SKILL.md" % name, "bytes": len(body)}
    return {"ok": False, "error": "could not find a SKILL.md at that source"}


if __name__ == "__main__":
    a = sys.argv[1:]
    print(import_skill(a[0] if a else "", a[1] if len(a) > 1 else None))
