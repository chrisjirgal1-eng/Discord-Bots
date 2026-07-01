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
    out = []
    for t in zoe_tools.TOOLS:
        if t["name"] in _EXCLUDE:
            continue
        params = list(((t.get("parameters") or {}).get("properties") or {}).keys())
        out.append({"name": t["name"], "desc": (t.get("description") or "").split(". ")[0][:90],
                    "params": params})
    return out


def _make_plan(task, tools):
    """Decompose a complex task into a SHORT ordered list of concrete subtasks mapped to tools."""
    try:
        import zoe_deep_research as dr
        dr.load_env()
        manifest = ", ".join(t["name"] for t in tools)
        ans = dr._openai([
            {"role": "system", "content":
             "You are Zoe's planner. Break the task into a SHORT ordered list of concrete subtasks (up "
             "to 6), each doable with ONE tool. Prefer the MOST DIRECT tool: use research or deep_dive "
             "to find or learn information (NOT browser_open/browser_type); use ecosystem_search for his "
             "own notes; use screen_task/browser_* only when a specific app or website must be operated. "
             "Return STRICT JSON {\"plan\": [{\"step\": short, \"tool\": name}]}. Use ONLY these tools: "
             + manifest + ". JSON only."},
            {"role": "user", "content": f"TASK: {task}\n\nPlan JSON:"}], max_tokens=500)
        m = re.search(r"\{.*\}", ans, re.S)
        d = json.loads(m.group(0)) if m else {}
        return d.get("plan", []) if isinstance(d, dict) else []
    except Exception:
        return []


def _next_step(task, tools, plan, history):
    """Pick the SINGLE next tool call against the plan + results so far, adapting on failure. JSON."""
    try:
        import zoe_deep_research as dr
        dr.load_env()
        manifest = "\n".join(f"- {t['name']}(args: {', '.join(t['params']) or 'none'}): {t['desc']}" for t in tools)
        plan_txt = "\n".join(f"{i + 1}. {p.get('step')} [{p.get('tool')}]" for i, p in enumerate(plan)) or "(none)"
        hist = "\n".join(f"{h['tool']}({h.get('args')}) -> {str(h.get('result'))[:110]}" for h in history[-6:])
        ans = dr._openai([
            {"role": "system", "content":
             "You are Zoe executing a task against a plan. Given the plan and the results so far, output "
             "STRICT JSON for the SINGLE next tool call: {\"tool\": name, \"args\": {...}, \"reason\": "
             "short} or {\"done\": true, \"summary\": short} when EVERY part of the task is complete. "
             "Follow the plan in order but ADAPT if a step failed (retry differently or use another "
             "tool). Prefer the MOST DIRECT tool: research or deep_dive to find/learn information (NOT "
             "browser_open/browser_type); ecosystem_search for his own notes; browser_*/screen_task "
             "only to operate a specific site or app. Use ONLY listed tools. Always include a valid "
             "\"tool\" or set done. JSON only."},
            {"role": "user", "content": f"TASK: {task}\n\nPLAN:\n{plan_txt}\n\nTOOLS:\n{manifest}\n\n"
             f"RESULTS SO FAR:\n{hist or 'none'}\n\nNext step JSON:"}], max_tokens=300)
        m = re.search(r"\{.*\}", ans, re.S)
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def accomplish(task, max_steps=8):
    """Plan the task, then execute + adapt against the plan until done or the step cap. Returns
    {ok, done, plan, steps, say}. Complex tasks get a real roadmap so subtasks are not dropped."""
    import zoe_tools
    task = (task or "").strip()
    if not task:
        return {"ok": False, "error": "no task"}
    tools = _toolset()
    names = {t["name"] for t in tools}
    plan = _make_plan(task, tools)
    history, stalls = [], 0
    for _ in range(max(1, min(int(max_steps or 8), 12))):
        step = _next_step(task, tools, plan, history)
        if not step:
            break
        if step.get("done"):
            return {"ok": True, "done": True, "plan": plan, "steps": history,
                    "say": step.get("summary", "Done, sir.")}
        tool, args = step.get("tool"), (step.get("args") or {})
        if tool not in names:
            stalls += 1
            if stalls >= 2:
                break
            continue
        res = zoe_tools.dispatch(tool, args, simulate=False)
        history.append({"tool": tool, "args": args, "reason": step.get("reason", ""),
                        "result": {k: res.get(k) for k in ("ok", "say", "needs_confirm", "error") if k in res}})
        if res.get("needs_confirm"):
            return {"ok": True, "done": False, "needs_confirm": True, "plan": plan, "steps": history,
                    "say": res.get("say", f"The '{tool}' step needs your yes, sir.")}
        stalls = 0 if res.get("ok") else stalls + 1
        if stalls >= 3:
            return {"ok": True, "done": False, "plan": plan, "steps": history,
                    "say": f"I hit a snag, sir; got through {len(history)} steps. Keep trying or take another angle?"}
    plan_txt = "; ".join(p.get("step", "") for p in plan[:4])
    return {"ok": True, "done": False, "plan": plan, "steps": history,
            "say": (f"My plan was {plan_txt}. I worked through {len(history)} steps toward it, sir."
                    if plan else f"Worked through {len(history)} steps, sir.")}


if __name__ == "__main__":
    import sys, pprint
    pprint.pprint(accomplish(" ".join(sys.argv[1:]) or "find the latest news about AI and remember the top headline"))
