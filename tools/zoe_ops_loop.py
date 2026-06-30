#!/usr/bin/env python3
"""ZOE Ops Loop: the local always-on loop, surfaced as a Zoe UI workspace (/ops).

Runs ONE task (default: a daily brief drafted from the memory bank), has a FRESH
pass verify it (the verifier is never the writer, per .claude/rules/verification.md),
and appends the result to memory-bank/ops-log.jsonl. Draft-only by construction: it
only generates text, it never takes an outward or irreversible action.

Engine = Zoe's own keys (Groq by default, OpenAI optional) via the same urllib
chat-completions pattern as zoe_router. No cloud host, no GitHub secrets needed.

  python tools/zoe_ops_loop.py            # run one cycle (what a scheduled task calls)
  python tools/zoe_ops_loop.py "task..."  # run one cycle with a one-off task

The server (tools/zoe_server.py) calls run_once() for the UI Run-now button and fires
it on a daily schedule while Zoe is open.
"""
import json, os, sys, time, datetime, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from jarvis_speak import load_env
except Exception:
    def load_env():
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "memory-bank", "ops-log.jsonl")
CFG = os.path.join(ROOT, "memory-bank", "ops-config.json")

DEFAULT_TASK = (
    "Run the daily JARVIS brief. From the memory-bank context below, pick ONE safe internal "
    "backlog item, draft it, and end with the single recommended next move and its follow-on "
    "effects. If the backlog is drained, say so plainly. Draft-only: never take an outward or "
    "irreversible action, you only produce text."
)

DEFAULTS = {
    "paused": False,
    "task": DEFAULT_TASK,
    "engine": "groq",                      # groq (free, default) or openai
    "model_groq": "llama-3.3-70b-versatile",
    "model_openai": "gpt-4o-mini",
    "max_tokens": 700,
    "schedule": "13:00",                   # local HH:MM daily fire
    "speak": True,                         # speak the brief aloud (ElevenLabs via jarvis_speak)
    "last_run_date": "",
}


def load_cfg():
    cfg = dict(DEFAULTS)
    try:
        with open(CFG, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_cfg(cfg):
    os.makedirs(os.path.dirname(CFG), exist_ok=True)
    keep = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
    with open(CFG, "w", encoding="utf-8") as f:
        json.dump(keep, f, indent=2)


def _chat(messages, cfg, max_tokens=None):
    """One chat-completion call, same urllib shape as zoe_router (User-Agent dodges the edge 403)."""
    engine = cfg.get("engine", "groq")
    if engine == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        url = "https://api.openai.com/v1/chat/completions"
        model = cfg.get("model_openai", DEFAULTS["model_openai"])
    else:
        key = os.environ.get("GROQ_API_KEY")
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = cfg.get("model_groq", DEFAULTS["model_groq"])
    if not key:
        raise RuntimeError(f"no API key in .env for engine '{engine}' (need {engine.upper()}_API_KEY)")
    body = json.dumps({
        "model": model, "messages": messages,
        "max_tokens": max_tokens or cfg.get("max_tokens", 700), "temperature": 0.4,
    }).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "User-Agent": "curl/8.19.0",
    })
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()


def read_context(limit=4000):
    parts = []
    for name in ("handoff.md", "active-context.md"):
        p = os.path.join(ROOT, "memory-bank", name)
        if os.path.exists(p):
            parts.append(f"### {name}\n" + open(p, encoding="utf-8").read()[:limit])
    return "\n\n".join(parts) or "(no memory-bank context found)"


def _spoken_brief(result, cfg):
    """A short JARVIS brief for the voice line, in the 'Wide awake, sir' style of the goal reel."""
    try:
        return _chat([
            {"role": "system", "content":
                "You are JARVIS giving Chris a spoken brief out loud. Two or three sentences, "
                "address him as sir, synthesize the key point and the single recommended next move, "
                "and end by asking what he would like handled first. No markdown, no lists, spoken prose."},
            {"role": "user", "content": f"Brief him based on this:\n{result[:1500]}"},
        ], cfg, max_tokens=170)
    except Exception:
        return ""


def speak_text(text):
    """Speak via jarvis_speak.py (ElevenLabs). Never raises: a voice failure must not break a run."""
    if not text:
        return False
    try:
        import subprocess
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_speak.py")
        subprocess.run([sys.executable, script, text], cwd=ROOT, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def run_once(task=None, speak=None):
    """Draft, verify with a fresh pass, build a spoken brief, log it, and optionally speak it."""
    load_env()
    cfg = load_cfg()
    task = (task or cfg.get("task") or DEFAULT_TASK).strip()
    ctx = read_context()
    started = time.time()
    spoken = ""
    try:
        draft = _chat([
            {"role": "system", "content":
                "You are JARVIS, Chris's AI ops loop. Be concise, concrete, and honest. "
                "Draft-only: you only produce text, you never take an outward or irreversible action."},
            {"role": "user", "content": f"{task}\n\nMEMORY-BANK CONTEXT:\n{ctx}"},
        ], cfg)
        verdict = _chat([
            {"role": "system", "content":
                "You are a FRESH reviewer. You did NOT write the draft below. Judge it on its own."},
            {"role": "user", "content":
                f"TASK:\n{task}\n\nDRAFT:\n{draft}\n\nIn 3 lines or fewer: is it correct, useful, "
                "and draft-only (no outward action taken)? Begin with PASS or NEEDS-WORK."},
        ], cfg, max_tokens=200)
        status = "PASS" if verdict.upper().lstrip().startswith("PASS") else "NEEDS-WORK"
        result, error = draft, ""
        spoken = _spoken_brief(draft, cfg)
    except Exception as e:
        status, result, verdict, error = "ERROR", "", "", str(e)
    rec = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "task": task[:240], "status": status, "result": result, "verdict": verdict,
        "spoken": spoken, "error": error, "engine": cfg.get("engine"),
        "secs": round(time.time() - started, 1),
    }
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    if status != "ERROR":
        cfg["last_run_date"] = datetime.date.today().isoformat()
        save_cfg(cfg)
    do_speak = cfg.get("speak", False) if speak is None else speak
    if do_speak and status != "ERROR" and spoken:
        speak_text(spoken)
    return rec


def read_log(n=25):
    if not os.path.exists(LOG):
        return []
    out = []
    for ln in open(LOG, encoding="utf-8").read().splitlines()[-n:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return list(reversed(out))


def status():
    cfg = load_cfg()
    last = read_log(1)
    return {
        "paused": cfg.get("paused", False), "task": cfg.get("task"),
        "engine": cfg.get("engine"), "schedule": cfg.get("schedule"),
        "max_tokens": cfg.get("max_tokens"), "last_run_date": cfg.get("last_run_date", ""),
        "speak": cfg.get("speak", False),
        "next_run": _next_run_str(cfg), "last": last[0] if last else None,
    }


def set_config(updates):
    cfg = load_cfg()
    for k in ("paused", "task", "engine", "schedule", "max_tokens", "speak"):
        if k in updates and updates[k] is not None:
            cfg[k] = updates[k]
    save_cfg(cfg)
    return status()


def _next_run_str(cfg):
    if cfg.get("paused"):
        return "paused"
    sched = cfg.get("schedule", "13:00")
    if cfg.get("last_run_date") == datetime.date.today().isoformat():
        return f"tomorrow {sched}"
    now = datetime.datetime.now().strftime("%H:%M")
    return f"today {sched}" if now < sched else "due now"


def should_autorun():
    cfg = load_cfg()
    if cfg.get("paused"):
        return False
    if cfg.get("last_run_date") == datetime.date.today().isoformat():
        return False
    return datetime.datetime.now().strftime("%H:%M") >= cfg.get("schedule", "13:00")


def serve_scheduler():
    """Background daily fire while Zoe is open. Safe: at most once per day, respects paused."""
    while True:
        try:
            if should_autorun():
                run_once()
        except Exception:
            pass
        time.sleep(60)


if __name__ == "__main__":
    load_env()
    args = list(sys.argv[1:])
    force = None
    if "--speak" in args:
        force = True; args.remove("--speak")
    if "--quiet" in args:
        force = False; args.remove("--quiet")
    rec = run_once(" ".join(args).strip() or None, speak=force)
    print(f"[{rec['status']}] {rec['ts']}  ({rec['secs']}s)")
    print(rec["result"][:1500] or rec["error"])
    if rec.get("spoken"):
        print("--- spoken ---"); print(rec["spoken"])
    print("--- verdict ---")
    print(rec["verdict"][:400])
