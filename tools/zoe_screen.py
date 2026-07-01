#!/usr/bin/env python3
"""Zoe's screen powers: SEE the screen (capture + vision) and CONTROL the desktop (mouse/keyboard).

Capture uses Pillow (built in). Control uses pyautogui. Used by zoe_tools (see_screen / control_screen).
Guardrail matches her other tools: a consequential control action is refused unless confirmed=True.

  python tools/zoe_screen.py see "what is on the screen"   # capture + describe (safe)
"""
import os, sys, time, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# typed text / keys that could be consequential -> refuse unless confirmed
_RISKY = ("rm ", "del ", "format", "shutdown", "restart", "rmdir", "uninstall", "drop table",
          "git push", "force", "sudo")


def capture(region=None):
    """Grab the screen to a temp PNG and return its path, or None on failure."""
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
        path = os.path.join(tempfile.gettempdir(), f"zoe-screen-{int(time.time()*1000)}.png")
        img.save(path)
        return path
    except Exception:
        return None


def see(query=""):
    """Capture the screen and describe it with OpenAI vision (read-only). Returns {ok, answer}."""
    path = capture()
    if not path:
        return {"ok": False, "error": "could not capture the screen"}
    try:
        import zoe_vision
        zoe_vision.load_env()
        r = zoe_vision.answer(path, query or "What is on the screen right now? Briefly, what matters most.")
        r["action"] = "see_screen"
        return r
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def _gui():
    import pyautogui
    pyautogui.FAILSAFE = True          # slam the mouse to a corner to abort
    pyautogui.PAUSE = 0.03
    return pyautogui


def click(x=None, y=None, button="left", double=False):
    try:
        g = _gui()
        b = "right" if button == "right" else "left"
        if x is not None and y is not None:
            g.doubleClick(int(x), int(y)) if double else g.click(int(x), int(y), button=b)
        else:
            g.doubleClick() if double else g.click(button=b)
        return {"ok": True, "action": "click", "x": x, "y": y, "button": b, "double": bool(double)}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def type_text(text, confirmed=False):
    t = str(text or "")
    if (not confirmed) and any(w in t.lower() for w in _RISKY):
        return {"ok": False, "needs_confirm": True, "error": "that looks consequential, confirm first", "text": t[:80]}
    try:
        _gui().typewrite(t, interval=0.01)
        return {"ok": True, "action": "type", "text": t[:80]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def press(keys, confirmed=False):
    k = str(keys or "").strip().lower()
    if not k:
        return {"ok": False, "error": "no key given"}
    try:
        g = _gui()
        if "+" in k:
            g.hotkey(*[p.strip() for p in k.split("+") if p.strip()])
        else:
            g.press(k)
        return {"ok": True, "action": "key", "keys": k}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def scroll(direction="down", amount=500):
    try:
        amt = abs(int(amount)) * (1 if str(direction).lower() == "up" else -1)
        _gui().scroll(amt)
        return {"ok": True, "action": "scroll", "direction": direction}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def volume(direction="up", steps=3):
    """System volume via media keys. direction up/down/mute. Safe (just media keys)."""
    try:
        g = _gui()
        d = str(direction).lower()
        if d in ("mute", "unmute", "toggle"):
            g.press("volumemute")
            return {"ok": True, "action": "volume", "did": "mute toggle"}
        key = "volumedown" if d in ("down", "lower", "quieter") else "volumeup"
        for _ in range(max(1, min(int(steps or 3), 10))):
            g.press(key)
        return {"ok": True, "action": "volume", "did": f"{d}"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def media(action="playpause"):
    """Media transport via keyboard media keys. play/pause, next, previous."""
    keys = {"playpause": "playpause", "play": "playpause", "pause": "playpause",
            "next": "nexttrack", "skip": "nexttrack", "previous": "prevtrack", "prev": "prevtrack"}
    try:
        _gui().press(keys.get(str(action).lower(), "playpause"))
        return {"ok": True, "action": "media", "did": action}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def save_screenshot():
    """Capture the screen and move it into the user's Pictures folder. Returns {ok, path}."""
    p = capture()
    if not p:
        return {"ok": False, "error": "could not capture the screen"}
    try:
        import shutil, datetime
        dest_dir = os.path.join(os.path.expanduser("~"), "Pictures")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, "zoe-shot-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".png")
        shutil.move(p, dest)
        return {"ok": True, "action": "screenshot", "path": dest}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _screen_size():
    try:
        import pyautogui
        return pyautogui.size()
    except Exception:
        try:
            from PIL import ImageGrab
            return ImageGrab.grab().size
        except Exception:
            return (1920, 1080)


# ---- Vision state machine: Look -> Plan -> Act -> Verify -> Repeat -----------------------------
_RISKY_WORDS = ("delete", "remove", "submit", "pay", "purchase", "buy", "send", "checkout", "confirm",
                "uninstall", "format", "shut down", "sign out", "log out", "post", "publish", "transfer")


def _looks_risky(plan):
    blob = (str(plan.get("action", "")) + " " + str(plan.get("text", "")) + " "
            + str(plan.get("keys", "")) + " " + str(plan.get("reason", ""))).lower()
    return bool(plan.get("risky")) or any(w in blob for w in _RISKY_WORDS)


def _guidance(plan):
    """Turn a planned action into a spoken directive for co-pilot (Guided) mode."""
    act = str(plan.get("action", "")).lower()
    reason = str(plan.get("reason", "")).strip()
    if act in ("click", "double_click", "right_click"):
        return f"Click {reason or 'the target'}" + (f", near the top" if (plan.get('y') or 999) < 300 else "") + "."
    if act == "type":
        return f"Type: {plan.get('text', '')}."
    if act == "key":
        return f"Press {plan.get('keys', '')}."
    if act == "scroll":
        return f"Scroll {plan.get('direction', 'down')}."
    return reason or "Do the next step."


def _log_step(task, phase, detail, status="ok"):
    """Stream each automation step into the Zoe OS activity log (the OS-tab monitoring view)."""
    try:
        import json as _j, datetime as _dt
        rec = {"ts": _dt.datetime.now().isoformat(timespec="seconds"), "resource": "screen_task",
               "phase": str(phase)[:24], "status": status, "detail": (str(detail) + " | " + task[:40])[:200]}
        with open(r"C:\Users\chris\Zoe\os\activity.jsonl", "a", encoding="utf-8") as f:
            f.write(_j.dumps(rec) + "\n")
    except Exception:
        pass


def _plan(task, shot_path, history, size, recover=False):
    """Vision model returns the SINGLE next action as JSON (with a risky flag). None on failure."""
    import re, json
    try:
        import zoe_vision
        zoe_vision.load_env()
    except Exception:
        return None
    w, h = size
    hist = "; ".join(f"{s.get('action')}@({s.get('x')},{s.get('y')}) changed={s.get('changed')}"
                     for s in history[-5:])
    extra = ("The LAST action did NOT change the screen as expected. Choose a DIFFERENT approach now: "
             "prefer a keyboard shortcut, Tab navigation, or a different target/coordinates. " if recover else "")
    q = ("You are operating this computer to accomplish: '%s'. %sLook at the screenshot and return the "
         "SINGLE next action as STRICT JSON ONLY, keys: action (click, double_click, type, key, scroll, "
         "done), x, y (integer pixel coords on this %dx%d screenshot for clicks), text (for type), keys "
         "(for key, e.g. 'enter','ctrl+s','tab'), direction (scroll up/down), reason (short: which "
         "element), risky (true if irreversible: delete, submit, send, pay, post), done (true when the "
         "task is complete). Prefer keyboard when reliable. Recent steps: %s. JSON only."
         % (task, extra, w, h, hist or "none"))
    r = zoe_vision.answer(shot_path, q)
    txt = (r.get("answer") if isinstance(r, dict) else "") or ""
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _verify(task, plan, after_shot):
    """Did the screen change toward the task after the action? Best-effort bool (default True)."""
    try:
        import zoe_vision
        zoe_vision.load_env()
        q = ("For the task '%s' I just did: %s (%s). Look at the screen NOW. Did that action move the "
             "task forward or change the screen as expected? Answer strictly YES or NO."
             % (task, plan.get("action"), str(plan.get("reason", ""))[:60]))
        r = zoe_vision.answer(after_shot, q)
        txt = ((r.get("answer") if isinstance(r, dict) else "") or "").strip().lower()
        return not txt.startswith("no")
    except Exception:
        return True


def _is_loop(history, plan):
    """True if this action repeats a recent one that did NOT change the screen (stuck)."""
    act = str(plan.get("action", "")).lower()
    ax, ay = plan.get("x"), plan.get("y")
    for s in history[-3:]:
        if s.get("action") == act and s.get("changed") is False:
            if act not in ("click", "double_click", "right_click"):
                return True
            try:
                if abs((s.get("x") or 0) - (ax or 0)) < 25 and abs((s.get("y") or 0) - (ay or 0)) < 25:
                    return True
            except Exception:
                pass
    return False


def _execute(act, plan):
    if act in ("click", "double_click", "right_click"):
        return click(plan.get("x"), plan.get("y"),
                     button=("right" if act == "right_click" else "left"), double=(act == "double_click"))
    if act == "type":
        return type_text(plan.get("text", ""))
    if act == "key":
        return press(plan.get("keys", ""))
    if act == "scroll":
        return scroll(plan.get("direction", "down"))
    return {"ok": False, "error": "unknown action " + act}


def do_task(task, max_steps=8, mode="auto", confirmed=False):
    """Robust visual automation: Look -> Plan -> Act -> Verify -> Repeat. Keeps a 5-step history to
    break loops, has autonomous (pause before irreversible) and guided (co-pilot) modes, and recovers
    from failed actions by trying alternatives. Returns {ok, done, steps, say, needs_confirm?, guided?}."""
    task = (task or "").strip()
    if not task:
        return {"ok": False, "error": "no task"}
    size = _screen_size()
    history, fails = [], 0
    _log_step(task, "start", f"mode={mode}", "start")
    for _ in range(max(1, min(int(max_steps or 8), 12))):
        shot = capture()                                            # LOOK
        if not shot:
            return {"ok": False, "error": "could not capture the screen", "steps": history}
        plan = _plan(task, shot, history, size, recover=(fails > 0))  # PLAN
        try:
            os.remove(shot)
        except Exception:
            pass
        if not plan:
            history.append({"action": "stop", "reason": "could not read the screen"})
            break
        act = str(plan.get("action") or "").lower()
        if plan.get("done") or act in ("done", "", "stop"):
            _log_step(task, "done", plan.get("reason", ""))
            return {"ok": True, "done": True, "steps": history, "say": str(plan.get("reason", "Done, sir."))[:120]}
        if mode == "guided":                                        # co-pilot: direct him, don't touch
            g = _guidance(plan)
            history.append({"action": "guide", "reason": g})
            _log_step(task, "guide", g)
            return {"ok": True, "done": False, "guided": True, "steps": history, "say": g}
        if _looks_risky(plan) and not confirmed:                    # AUTONOMOUS: pause before irreversible
            _log_step(task, "pause", plan.get("reason", ""), "warn")
            return {"ok": True, "done": False, "needs_confirm": True, "steps": history,
                    "say": f"The next step looks irreversible ({plan.get('reason', '')}). Say yes and I'll do it."}
        if _is_loop(history, plan):                                 # loop guard
            fails += 1
            if fails >= 3:
                _log_step(task, "loop", "stuck", "error")
                return {"ok": True, "done": False, "steps": history,
                        "say": "That control isn't responding, sir; I'm looping. Want to guide me?"}
        r = _execute(act, plan)                                     # ACT
        after = capture()
        changed = _verify(task, plan, after) if after else True     # VERIFY
        try:
            os.remove(after)
        except Exception:
            pass
        history.append({"action": act, "x": plan.get("x"), "y": plan.get("y"),
                        "reason": str(plan.get("reason", ""))[:80], "ok": r.get("ok"), "changed": changed})
        _log_step(task, act, plan.get("reason", ""), "ok" if changed else "warn")
        fails = 0 if changed else fails + 1                         # REPEAT / recover
        if fails >= 3:
            return {"ok": True, "done": False, "steps": history,
                    "say": "I tried a few different ways but the screen isn't changing as expected, sir. "
                           "Want to take over, or should I guide you?"}
        time.sleep(0.6)
    return {"ok": True, "done": False, "steps": history, "say": f"Worked through {len(history)} steps, sir."}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "see":
        print(see(" ".join(sys.argv[2:])))
    elif len(sys.argv) > 1 and sys.argv[1] == "task":
        import pprint
        pprint.pprint(do_task(" ".join(sys.argv[2:])))
    else:
        p = capture()
        print({"captured": p, "exists": bool(p and os.path.isfile(p))})
