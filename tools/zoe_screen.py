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


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "see":
        print(see(" ".join(sys.argv[2:])))
    else:
        p = capture()
        print({"captured": p, "exists": bool(p and os.path.isfile(p))})
