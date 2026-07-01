#!/usr/bin/env python3
"""Import a skill (its SKILL.md playbook) from a public GitHub repo into Zoe's .claude/skills, so
use_skill can run it. Inspired by OpenJarvis skill import. SAFE: only the markdown playbook is
downloaded -- no scripts are fetched or executed -- so importing a skill just adds instructions.

  python tools/zoe_skill_import.py owner/repo skill-name
  python tools/zoe_skill_import.py https://github.com/owner/repo/blob/main/skills/foo/SKILL.md foo
"""
import os, sys, re, json, urllib.request

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


def sync_skills(repo, path="skills", limit=10):
    """Bulk-import up to `limit` skills from owner/repo's `path` dir (each one's SKILL.md), via the
    GitHub contents API. Only markdown playbooks are downloaded. Returns {ok, imported, count, found}."""
    m = re.match(r"^([^/\s]+)/([^/\s]+)$", (repo or "").strip())
    if not m:
        return {"ok": False, "error": "give an owner/repo"}
    o, rp = m.groups()
    body = None
    for p in (path, ".claude/skills", "src/skills"):                  # try a few common skill roots
        body = _get("https://api.github.com/repos/%s/%s/contents/%s" % (o, rp, p.strip("/")))
        if body and body.lstrip().startswith("["):
            path = p
            break
    if not body:
        return {"ok": False, "error": f"could not list skills in {repo}"}
    try:
        items = json.loads(body)
    except Exception:
        return {"ok": False, "error": "could not parse the repo listing"}
    dirs = [it.get("name") for it in items if isinstance(it, dict) and it.get("type") == "dir"]
    imported = []
    for name in dirs[:max(1, min(int(limit or 10), 25))]:
        r = import_skill("%s/%s" % (o, rp), name) if path == "skills" else \
            _install_from(o, rp, "%s/%s/SKILL.md" % (path, name), name)
        if r.get("ok"):
            imported.append(r["name"])
    return {"ok": bool(imported), "imported": imported, "count": len(imported), "found": len(dirs)}


def _install_from(owner, repo, relpath, name):
    """Install a SKILL.md from an explicit repo path (used by sync_skills for non-default roots)."""
    for br in ("main", "master"):
        body = _get("https://raw.githubusercontent.com/%s/%s/%s/%s" % (owner, repo, br, relpath))
        if body and len(body.strip()) > 20:
            d = os.path.join(SKILLS, _slug(name))
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(body)
            return {"ok": True, "name": _slug(name)}
    return {"ok": False}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "sync":
        print(sync_skills(a[1] if len(a) > 1 else ""))
    else:
        print(import_skill(a[0] if a else "", a[1] if len(a) > 1 else None))
