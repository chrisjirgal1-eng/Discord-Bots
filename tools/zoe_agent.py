#!/usr/bin/env python3
"""Zoe's general task agent: take ANY task, plan it, and execute it step by step by chaining her own
tools until it's done or a step cap. Irreversible tool actions self-gate (they return needs_confirm),
so nothing runs away. Never raises.
"""
import json, re

# tools that modify the system / code are kept OUT of autonomous chains for safety; ask for them directly
_EXCLUDE = {"accomplish", "self_evolve", "build_feature", "merge_build", "run_command", "ecosystem_run"}


def _toolset():
    import zoe_tools
    return [{"name": t["name"], "desc": (t.get("description") or "").split(". ")[0][:100]}
            for t in zoe_tools.TOOLS if t["name"] not in _EXCLUDE]


def _next_step(task, tools, history):
    """Model picks the single next tool call as JSON, or {done: true}. None on failure."""
    try:
        import zoe_deep_research as dr
        dr.load_env()
        manifest = "\n".join(f"- {t['name']}: {t['desc']}" for t in tools)
        hist = "\n".join(f"{h['tool']}({h.get('args')}) -> {str(h.get('result'))[:120]}" for h in history[-6:])
        ans = dr._openai([
            {"role": "system", "content":
             "You are Zoe's task executor. Given the task, your available tools, and the results so far, "
             "output STRICT JSON for the SINGLE next step: {\"tool\": name, \"args\": {...}, \"reason\": "
             "short} or {\"done\": true, \"summary\": short} when the task is complete or cannot proceed. "
             "Complete EVERY part of the task before saying done (e.g. if it says find X and remember it, "
             "after finding, the next step is remember). Use ONLY the listed tools; pick the most direct "
             "one. Always include a valid \"tool\" or set done. JSON only."},
            {"role": "user", "content": f"TASK: {task}\n\nTOOLS:\n{manifest}\n\nRESULTS SO FAR:\n"
             f"{hist or 'none'}\n\nNext step JSON:"}], max_tokens=300)
        m = re.search(r"\{.*\}", ans, re.S)
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def accomplish(task, max_steps=6):
    """Plan + execute with Zoe's tools until done or the step cap. Returns {ok, done, steps, say}."""
    import zoe_tools
    task = (task or "").strip()
    if not task:
        return {"ok": False, "error": "no task"}
    tools = _toolset()
    names = {t["name"] for t in tools}
    history = []
    for _ in range(max(1, min(int(max_steps or 6), 10))):
        step = _next_step(task, tools, history)
        if not step:
            break
        if step.get("done"):
            return {"ok": True, "done": True, "steps": history, "say": step.get("summary", "Done, sir.")}
        tool, args = step.get("tool"), (step.get("args") or {})
        if tool not in names:
            break                               # no valid next tool -> stop cleanly (keep progress)
        res = zoe_tools.dispatch(tool, args, simulate=False)
        history.append({"tool": tool, "args": args, "reason": step.get("reason", ""),
                        "result": {k: res.get(k) for k in ("ok", "say", "needs_confirm", "error") if k in res}})
        if res.get("needs_confirm"):
            return {"ok": True, "done": False, "steps": history, "needs_confirm": True,
                    "say": res.get("say", f"The '{tool}' step needs your yes before I go on, sir.")}
    return {"ok": True, "done": False, "steps": history,
            "say": f"I worked through {len(history)} steps toward that, sir."}


if __name__ == "__main__":
    import sys, pprint
    pprint.pprint(accomplish(" ".join(sys.argv[1:]) or "find the latest news about AI and remember the top headline"))
