#!/usr/bin/env python3
"""ZOE learned-corrections store (memory/learned_routes.json).

The piece that lets ZOE actually evolve: once she's corrected on a phrasing, that mapping is
stored here and the router applies it BEFORE the LLM — so she never repeats that mistake and the
right action is instant. Data-level learning ONLY (safe, reversible); it never rewrites code.

Best-effort, atomic, never raises (so it can't break the command pipeline). Pure stdlib.
"""
import os, json, re, time, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "memory", "learned_routes.json")
_FILLERS = {"please", "zoe", "zoey", "hey", "ok", "okay", "could", "you", "can", "would",
            "pls", "just", "um", "uh", "the", "a", "to", "for", "me", "my"}
_FUZZY = 0.6   # token-overlap threshold for a near-variant to match a learned phrase


def _norm(text):
    toks = [w for w in re.sub(r"[^a-z0-9 ]", " ", (text or "").lower()).split()
            if w and w not in _FILLERS]
    return " ".join(toks)


def _load():
    try:
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d):
    try:
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(STORE), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
        os.replace(tmp, STORE)               # atomic
        return True
    except Exception:
        return False


def learn(phrase, action, source="correction"):
    """Store/refresh a learned route: normalized phrase -> action dict. Returns the key, '' on fail."""
    try:
        key = _norm(phrase)
        if not key or not isinstance(action, dict) or not action.get("action"):
            return ""
        d = _load()
        prev = d.get(key, {})
        d[key] = {"action": action.get("action"), "target": action.get("target"),
                  "url": action.get("url"), "say": action.get("say"),
                  "raw": phrase, "source": source, "hits": int(prev.get("hits", 0)),
                  "learned_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        _save(d)
        return key
    except Exception:
        return ""


def _overlap(a, b):
    sa, sb = set(a.split()), set(b.split())
    return len(sa & sb) / len(sa | sb) if sa and sb else 0.0


def lookup(text):
    """Learned action for this phrase (exact normalized, else best fuzzy >= threshold), bumping the
    hit count. None if nothing learned matches. Best-effort, never raises."""
    try:
        key = _norm(text)
        if not key:
            return None
        d = _load()
        hit = key if key in d else None
        if not hit:
            best, score = None, 0.0
            for k in d:
                s = _overlap(key, k)
                if s > score:
                    best, score = k, s
            if best and score >= _FUZZY:
                hit = best
        if not hit:
            return None
        rec = d[hit]
        rec["hits"] = int(rec.get("hits", 0)) + 1
        _save(d)
        return {"action": rec.get("action"), "target": rec.get("target"), "url": rec.get("url"),
                "say": rec.get("say") or "On it, sir.", "_learned": hit}
    except Exception:
        return None


def forget(phrase):
    try:
        d = _load(); key = _norm(phrase)
        if key in d:
            del d[key]; _save(d); return True
        return False
    except Exception:
        return False


def all():
    return _load()


if __name__ == "__main__":
    print(json.dumps(_load(), indent=2))
