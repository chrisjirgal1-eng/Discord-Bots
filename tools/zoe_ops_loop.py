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
import json, os, re, subprocess, sys, time, datetime, urllib.request
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
    "actor": "edit",                       # "edit" = Groq find/replace (safe, tested); "claude" = claude -p
    "max_turns_act": 12,                   # turn cap for the claude actor
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
                "You are Zoe giving Chris a quick spoken update, like a sharp teammate, not a formal "
                "butler. Default to ONE short, casual, warm line, for example 'Hey sir, handled the "
                "daily brief, nothing urgent.' Only go longer (two or three sentences with the "
                "recommended next move) if the result is genuinely complex or needs his decision. "
                "Address him as sir or Chris. No markdown, no lists, spoken prose."},
            {"role": "user", "content": f"Update him based on this:\n{result[:1500]}"},
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


# ----- ACT mode: the loop makes the change for real, on an isolated branch, tests it, commits if
# green. It never pushes, never merges, never touches your working tree (uses a git worktree off
# HEAD), and never runs on the schedule. Manual trigger only (UI Build button or `--act`).
DENY = (".env", ".git/", "cookies", "secret", "ig_cookies", "id_rsa", ".pem", "node_modules",
        "package-lock", ".github/workflows")
# Reject AI tells in a proposed edit. The dash is matched via its escape so this file holds no
# literal one; the words below are detection targets, not prose.
_BANNED_RX = re.compile(chr(0x2014) + r"|\b(?:leverage|delve|fantastic|seamless)\b")


def _git(args, timeout=120):
    return subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)


def _safe_path(path):
    p = str(path).replace("\\", "/").lstrip("/")
    if not p or ".." in p.split("/"):
        return False
    if any(d in p.lower() for d in DENY):
        return False
    full = os.path.normpath(os.path.join(ROOT, p))
    return (full == ROOT or full.startswith(ROOT + os.sep)) and os.path.isfile(full)


def _propose_change(task, ctx, cfg):
    sys_p = (
        "You are JARVIS in ACT mode. Propose ONE small, safe, internal code or doc change that moves "
        "the task forward. Reply with STRICT JSON and nothing else: "
        '{"no_change": false, "summary": "<one line>", "path": "<repo-relative file>", '
        '"find": "<exact text that appears EXACTLY ONCE in the file>", "replace": "<new text>"} '
        'or {"no_change": true, "why": "<reason>"}. Keep the change tiny and reversible. Never touch '
        ".env, secrets, cookies, .git, node_modules, or workflows. No em dashes or AI-tell words."
    )
    raw = _chat([{"role": "system", "content": sys_p},
                 {"role": "user", "content": f"TASK: {task}\n\nCONTEXT:\n{ctx[:3000]}"}], cfg, max_tokens=900)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else {"no_change": True, "why": "model returned no JSON"}
    except Exception:
        return {"no_change": True, "why": "model JSON did not parse"}


def _safe_changed(path):
    """Path-string safety for files a change touched (no main-tree existence needed; new files ok)."""
    p = str(path).replace("\\", "/").lstrip("/")
    if not p or ".." in p.split("/"):
        return False
    return not any(d in p.lower() for d in DENY)


def _act_claude(task, speak=None):
    """ACT via the claude CLI as a stronger actor, inside the isolated worktree. Safer than raw
    skip-permissions: acceptEdits + no Bash tool (so no commands/push/network), plus a tamper check
    that aborts if claude touches anything outside the sandbox. Needs a one-time `claude /login`."""
    load_env()
    cfg = load_cfg()
    task = (task or cfg.get("task") or DEFAULT_TASK).strip()
    started = time.time()
    ts = datetime.datetime.now()
    branch = "ops/auto-" + ts.strftime("%Y%m%d-%H%M%S")
    wt = os.path.join(ROOT, ".ops-worktrees", ts.strftime("%H%M%S"))
    status, result, verdict, spoken, keep = "NEEDS-WORK", "", "", "", False
    main_before = _git(["status", "--porcelain"]).stdout
    try:
        add = _git(["worktree", "add", "-b", branch, wt, "HEAD"])
        if add.returncode != 0:
            status, result = "ERROR", "worktree add failed: " + add.stderr[:300]
        else:
            prompt = ("You are JARVIS in ACT mode, working inside an isolated git worktree. Make ONE small, "
                      "safe, internal change that advances the task, editing files in THIS directory only. "
                      "Do not run git, do not push, do not touch .env, secrets, cookies, or .github. Stop when "
                      f"done.\n\nTASK: {task}")
            try:
                cp = subprocess.run(
                    ["claude", "-p", prompt, "--max-turns", str(cfg.get("max_turns_act", 12)),
                     "--permission-mode", "acceptEdits", "--allowedTools", "Read Edit Write Grep Glob"],
                    cwd=wt, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
                out = (cp.stdout + cp.stderr)
            except FileNotFoundError:
                out = "claude CLI not found on PATH"
            except Exception as e:
                out = "claude run error: " + str(e)
            low = out.lower()
            if "not logged in" in low or "please run /login" in low or "not been trusted" in low or "not found" in low:
                result = ("Claude actor needs a one-time setup: open a terminal in the repo, run `claude`, do "
                          "/login, and accept the trust prompt. Then set actor=claude and try again.")
            else:
                main_after = _git(["status", "--porcelain"]).stdout
                if main_after != main_before:
                    status, result = "ERROR", ("ABORTED: the Claude actor changed files OUTSIDE the sandbox "
                                               "worktree. Nothing was committed. Check your working tree.")
                else:
                    diff = _git(["-C", wt, "diff"]).stdout
                    porc = _git(["-C", wt, "status", "--porcelain"]).stdout
                    if not diff.strip() and not porc.strip():
                        result = "Claude made no change.\n" + out[-400:]
                    else:
                        changed = [ln[3:] for ln in porc.splitlines() if ln[3:]]
                        bad = [p for p in changed if not _safe_changed(p)]
                        if bad:
                            result = "Rejected: change touched denylisted paths: " + ", ".join(bad[:5])
                        else:
                            try:
                                tr = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=wt,
                                                    capture_output=True, text=True, timeout=900)
                                tests_ok = tr.returncode == 0
                                tail = "\n".join((tr.stdout + tr.stderr).strip().splitlines()[-5:])
                            except Exception as te:
                                tests_ok, tail = False, "tests could not run: " + str(te)[:150]
                            verdict = _chat([
                                {"role": "system", "content": "You are a FRESH reviewer. You did NOT write this diff."},
                                {"role": "user", "content": f"TASK: {task}\n\nDIFF:\n{diff[:2500]}\n\npytest passed: "
                                 f"{tests_ok}\n\nIn 3 lines: PASS or NEEDS-WORK and the key risk."}], cfg, max_tokens=180)
                            review_ok = verdict.upper().lstrip().startswith("PASS")
                            if tests_ok and review_ok:
                                _git(["-C", wt, "add", "-A"])
                                _git(["-C", wt, "commit", "-m",
                                      f"ops(auto, claude): {task[:60]}\n\nAutonomous Ops Loop change via the Claude "
                                      "actor on an isolated branch. Review before merging; not pushed.\n\n"
                                      "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"])
                                status, keep = "PASS", True
                                result = (f"Shipped on branch {branch} (Claude actor)\n  files: "
                                          f"{', '.join(changed[:6])}\n  tests green, review pass\n{tail}")
                            else:
                                result = (f"Reverted, not committed. tests={'green' if tests_ok else 'red'} "
                                          f"review={'pass' if review_ok else 'fail'}\n{tail}")
        spoken = _spoken_brief(result, cfg) if status != "ERROR" else ""
    except Exception as e:
        status, result = "ERROR", str(e)[:400]
    finally:
        try:
            if os.path.isdir(wt):
                _git(["worktree", "remove", wt, "--force"])
        except Exception:
            pass
        if not keep:
            try:
                _git(["branch", "-D", branch])
            except Exception:
                pass
    rec = {"ts": ts.isoformat(timespec="seconds"), "task": task[:240], "mode": "act-claude",
           "branch": branch if keep else "", "status": status, "result": result, "verdict": verdict,
           "spoken": spoken, "error": result if status == "ERROR" else "",
           "engine": "claude", "secs": round(time.time() - started, 1)}
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    cfg["last_run_date"] = datetime.date.today().isoformat()
    save_cfg(cfg)
    do_speak = cfg.get("speak", True) if speak is None else speak
    if do_speak and spoken:
        speak_text(spoken)
    return rec


def act_once(task=None, speak=None, actor=None):
    """Make the change on an isolated worktree branch, test it, commit only if green. Never pushes."""
    load_env()
    cfg = load_cfg()
    if (actor or cfg.get("actor", "edit")) == "claude":
        return _act_claude(task, speak)
    task = (task or cfg.get("task") or DEFAULT_TASK).strip()
    started = time.time()
    ts = datetime.datetime.now()
    branch = "ops/auto-" + ts.strftime("%Y%m%d-%H%M%S")
    wt = os.path.join(ROOT, ".ops-worktrees", ts.strftime("%H%M%S"))
    status, result, verdict, spoken, keep = "NEEDS-WORK", "", "", "", False
    try:
        prop = _propose_change(task, read_context(), cfg)
        if prop.get("no_change"):
            result = "No change proposed. " + str(prop.get("why", ""))[:300]
        else:
            path, find, replace = str(prop.get("path", "")), prop.get("find", ""), str(prop.get("replace", ""))
            if not find or not _safe_path(path):
                result = f"Rejected unsafe or invalid edit target: {path!r}"
            elif _BANNED_RX.search(replace):
                result = "Rejected: the proposed edit contained a banned word or em dash."
            else:
                add = _git(["worktree", "add", "-b", branch, wt, "HEAD"])
                if add.returncode != 0:
                    status, result = "ERROR", "worktree add failed: " + add.stderr[:300]
                else:
                    fp = os.path.join(wt, path.replace("\\", "/"))
                    src = open(fp, encoding="utf-8").read()
                    if src.count(find) != 1:
                        result = f"Find text appears {src.count(find)} times in {path} (need exactly 1). Reverted."
                    else:
                        open(fp, "w", encoding="utf-8").write(src.replace(find, replace, 1))
                        diff = _git(["-C", wt, "diff"]).stdout
                        try:
                            tr = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=wt,
                                                capture_output=True, text=True, timeout=600)
                            tests_ok = tr.returncode == 0
                            tail = "\n".join((tr.stdout + tr.stderr).strip().splitlines()[-5:])
                        except Exception as te:
                            tests_ok, tail = False, "tests could not run: " + str(te)[:150]
                        verdict = _chat([
                            {"role": "system", "content": "You are a FRESH reviewer. You did NOT write this diff."},
                            {"role": "user", "content": f"TASK: {task}\n\nDIFF:\n{diff[:2500]}\n\npytest passed: "
                             f"{tests_ok}\n\nIn 3 lines: PASS or NEEDS-WORK and the key risk."}], cfg, max_tokens=180)
                        review_ok = verdict.upper().lstrip().startswith("PASS")
                        if tests_ok and review_ok:
                            _git(["-C", wt, "add", "-A"])
                            _git(["-C", wt, "commit", "-m",
                                  f"ops(auto): {str(prop.get('summary', 'change'))[:60]}\n\nAutonomous Ops Loop "
                                  "change on an isolated branch. Review before merging; not pushed.\n\n"
                                  "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"])
                            status, keep = "PASS", True
                            result = (f"Shipped on branch {branch}\n  {path}: {prop.get('summary', '')}\n"
                                      f"  tests green, review pass\n{tail}")
                        else:
                            result = (f"Reverted, not committed. tests={'green' if tests_ok else 'red'} "
                                      f"review={'pass' if review_ok else 'fail'}\n  {path}: "
                                      f"{prop.get('summary', '')}\n{tail}")
        spoken = _spoken_brief(result, cfg) if status != "ERROR" else ""
    except Exception as e:
        status, result = "ERROR", str(e)[:400]
    finally:
        try:
            if os.path.isdir(wt):
                _git(["worktree", "remove", wt, "--force"])
        except Exception:
            pass
        if not keep:
            try:
                _git(["branch", "-D", branch])
            except Exception:
                pass
    rec = {"ts": ts.isoformat(timespec="seconds"), "task": task[:240], "mode": "act",
           "branch": branch if keep else "", "status": status, "result": result, "verdict": verdict,
           "spoken": spoken, "error": result if status == "ERROR" else "",
           "engine": cfg.get("engine"), "secs": round(time.time() - started, 1)}
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    cfg["last_run_date"] = datetime.date.today().isoformat()
    save_cfg(cfg)
    do_speak = cfg.get("speak", True) if speak is None else speak
    if do_speak and spoken:
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
        "speak": cfg.get("speak", False), "actor": cfg.get("actor", "edit"),
        "next_run": _next_run_str(cfg), "last": last[0] if last else None,
    }


def set_config(updates):
    cfg = load_cfg()
    for k in ("paused", "task", "engine", "schedule", "max_tokens", "speak", "actor", "max_turns_act"):
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
    do_act = "--act" in args
    if do_act:
        args.remove("--act")
    force_actor = None
    if "--claude" in args:                 # force the claude actor for this run (implies --act)
        force_actor = "claude"; do_act = True; args.remove("--claude")
    if "--speak" in args:
        force = True; args.remove("--speak")
    if "--quiet" in args:
        force = False; args.remove("--quiet")
    _task = " ".join(args).strip() or None
    rec = act_once(_task, speak=force, actor=force_actor) if do_act else run_once(_task, speak=force)
    print(f"[{rec['status']}] {rec['ts']}  ({rec['secs']}s)")
    print(rec["result"][:1500] or rec["error"])
    if rec.get("spoken"):
        print("--- spoken ---"); print(rec["spoken"])
    print("--- verdict ---")
    print(rec["verdict"][:400])
