#!/usr/bin/env python3
"""ZOE evolution engine (Part B). Reviews what she got wrong + what she's already learned and asks
HERMES (the local Nous agent) — Groq fallback — to propose GENERAL improvements: new phrasing->action
rules, app names to register in apps.json, fast-path regex patterns. Writes an 'Evolution Proposals'
vault note.

Safety: code-level proposals are NOT auto-applied (only the data layer, learned_routes, auto-evolves).
Best-effort, never raises. Run on demand or at session end. Run: python tools/zoe_evolve.py
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_review
except Exception:
    zoe_review = None
try:
    import zoe_learn
except Exception:
    zoe_learn = None
try:
    import zoe_memory
except Exception:
    zoe_memory = None
try:
    import zoe_router
except Exception:
    zoe_router = None

_PROMPT = ("You tune a Windows voice assistant's command router. Given (a) recent mistakes/corrections "
           "and (b) routes it already learned, propose up to 5 GENERAL improvements: new phrasing->action "
           "rules, app names to register in apps.json, or fast-path regex patterns. Concrete and short. "
           "Bullet list only, no preamble.")


def _ask_hermes(prompt):
    """Try the local Hermes agent via the existing plugin. Returns answer text or None if unhandled/absent."""
    if not zoe_router:
        return None
    try:
        cmd = zoe_router.make_command(intent="plugin_action", target="hermes", payload={"prompt": prompt})
        handled, res = zoe_router._run_plugin(cmd)
        if handled and isinstance(res, dict) and res.get("answer"):
            return res["answer"]
    except Exception:
        pass
    return None


def _ask_groq(prompt, groq_key):
    if not groq_key:
        return None
    try:
        import urllib.request
        body = json.dumps({"model": "llama-3.1-8b-instant", "temperature": 0.4, "max_tokens": 350,
                           "messages": [{"role": "system", "content": _PROMPT},
                                        {"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json",
                     "User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def run(write_note=True):
    """Generalize recent mistakes + learned routes into proposals (Hermes, else Groq) and write a
    vault note. Returns {source, proposals, ...}. Best-effort, never raises."""
    try:
        metrics = zoe_review.analyze() if zoe_review else {}
        learned = zoe_learn.all() if zoe_learn else {}
        if not (metrics.get("corrections") or metrics.get("failures") or metrics.get("fallbacks") or learned):
            return {"source": "none", "proposals": "No new signals to evolve from."}
        ctx = json.dumps({"corrections": metrics.get("corrections"), "failures": metrics.get("failures"),
                          "fallbacks": metrics.get("fallbacks"), "app_misses": metrics.get("app_misses"),
                          "already_learned": list(learned.keys())})
        prompt = _PROMPT + "\n\nDATA:\n" + ctx
        ans, source = _ask_hermes(prompt), "hermes"
        if not ans:
            ans, source = _ask_groq(prompt, os.environ.get("GROQ_API_KEY")), "groq"
        if not ans:
            return {"source": "none", "proposals": "(Hermes and Groq both unavailable)"}
        if write_note and zoe_memory:
            body = (f"_Auto-generated {time.strftime('%Y-%m-%d %H:%M')} via {source}. "
                    f"{len(learned)} learned route(s), {len(metrics.get('corrections', []))} correction(s)._\n\n"
                    "## Proposed improvements\n_Review before applying — code changes are NOT auto-applied._\n\n"
                    + ans + "\n\n## Already learned (auto-applied)\n"
                    + "\n".join(f"- `{k}` -> {v.get('action')} {v.get('target') or v.get('url') or ''}"
                                for k, v in learned.items()))
            zoe_memory.write("Evolution Proposals", body, folder="project", tags=["evolution", "proposals", "auto"])
        return {"source": source, "proposals": ans, "learned": len(learned)}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
