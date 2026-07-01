#!/usr/bin/env python3
"""ZOE self-improvement monitor (Phase 4).

Reviews recent command history + logged corrections to surface where she's weak — corrections
("that's not what I meant"), failed commands, repeated retries, and chat-fallbacks for
command-like phrases — and writes a 'Self-Review' note to the vault with concrete, actionable
suggestions (apps to register, phrasings to route better, fast-path rules to add).

Read-only on state, best-effort, never raises. Run on demand or at session end (the voice loop
calls it on shutdown). Run: python tools/zoe_review.py
"""
import os, sys, json, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_state
except Exception:
    zoe_state = None
try:
    import zoe_memory
except Exception:
    zoe_memory = None


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def analyze():
    """Pure weakness analysis from persisted state. Returns a metrics dict."""
    st = zoe_state.load() if zoe_state else {}
    hist = (st.get("history", {}) or {}).get("last_commands", []) or st.get("last_commands", [])
    conv = st.get("conversation", {}) or {}
    corrections = [c.get("text") for c in (conv.get("corrections") or [])]
    failures = [c.get("text") for c in hist if c.get("handled") is False]
    fallbacks = [c.get("text") for c in hist
                 if c.get("action") == "chat" and len(_norm(c.get("text")).split()) >= 2]
    seen, retries = {}, []
    for c in hist:
        n = _norm(c.get("text"))
        if n and n in seen:
            retries.append(c.get("text"))
        seen[n] = seen.get(n, 0) + 1
    app_misses = []
    for c in hist:
        if c.get("handled") is False and c.get("action") in ("launch", "close"):
            parts = (c.get("text") or "").split()
            if parts:
                app_misses.append(parts[-1])
    return {
        "total": len(hist),
        "failures": failures[-10:],
        "corrections": corrections[-10:],
        "fallbacks": fallbacks[-10:],
        "retries": list(dict.fromkeys(retries))[-10:],
        "app_misses": sorted(set(app_misses)),
        "fallback_rate": round(len(fallbacks) / max(len(hist), 1), 2),
    }


def suggest(m, groq_key=None):
    """Rule-based suggestions + optional Groq enrichment. Returns a list of strings."""
    s = []
    if m["app_misses"]:
        s.append(f"Register these unresolved apps in electron/config/apps.json: {', '.join(m['app_misses'])}.")
    if m["corrections"]:
        s.append(f"{len(m['corrections'])} correction(s) — tune routing for: " + "; ".join(m["corrections"][:5]))
    if m["fallbacks"] and m["fallback_rate"] > 0.3:
        s.append(f"High chat-fallback rate ({m['fallback_rate']}). Command-like phrases routed to chat: "
                 + "; ".join(m["fallbacks"][:5]) + " — extend INTENT_SYS or _fast_classify in zoe_router.")
    if m["retries"]:
        s.append("Repeated commands (likely retries she got wrong): " + "; ".join(m["retries"][:5]))
    if not s:
        s.append("No weaknesses detected in recent history — routing looks healthy.")
    groq_key = groq_key or os.environ.get("GROQ_API_KEY")
    if groq_key and (m["corrections"] or m["fallbacks"]):
        try:
            import urllib.request
            payload = {"model": "llama-3.1-8b-instant", "temperature": 0.3, "max_tokens": 200,
                "messages": [{"role": "system", "content": "You tune a voice assistant's command router. "
                              "Given examples it mishandled, give up to 3 SHORT concrete fixes (new routing "
                              "rules, app names to register, phrasings to map). Bullet list only."},
                             {"role": "user", "content": json.dumps({k: m[k] for k in
                              ("corrections", "fallbacks", "app_misses")})}]}
            req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json",
                         "User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=15) as r:
                s.append("AI suggestions:\n" + json.load(r)["choices"][0]["message"]["content"].strip())
        except Exception:
            pass
    return s


def review(write_note=True):
    """Analyze + suggest + (optionally) write a vault note. Returns {metrics, suggestions}. Best-effort."""
    try:
        m = analyze()
        sugg = suggest(m)
        if write_note and zoe_memory:
            body = (f"_Auto-generated {time.strftime('%Y-%m-%d %H:%M')}. Reviewed {m['total']} recent commands._\n\n"
                    f"## Signals\n- failures: {len(m['failures'])}\n- corrections: {len(m['corrections'])}\n"
                    f"- chat-fallbacks: {len(m['fallbacks'])} (rate {m['fallback_rate']})\n- retries: {len(m['retries'])}\n\n"
                    "## Suggested improvements\n" + "\n".join(f"- {x}" for x in sugg))
            zoe_memory.write("Self-Review", body, folder="project", tags=["self-review", "auto"])
        return {"metrics": m, "suggestions": sugg}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print(json.dumps(review(), indent=2))
