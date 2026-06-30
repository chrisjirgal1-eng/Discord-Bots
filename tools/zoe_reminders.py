#!/usr/bin/env python3
"""Zoe's reminders: a tiny time-based reminder store. The voice's idle loop checks due() and
speaks any reminder whose time has arrived. Bounded by design -- she only fires what Chris
explicitly set, at the time he set, so there is no random chatter or wasted cost.

  python tools/zoe_reminders.py add "call the coach" 30      # remind in 30 minutes
"""
import os, sys, json, time, datetime, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "memory", "reminders.json")


def _load():
    try:
        return json.load(open(STORE, encoding="utf-8"))
    except Exception:
        return []


def _save(items):
    try:
        os.makedirs(os.path.dirname(STORE), exist_ok=True)
        json.dump(items, open(STORE, "w", encoding="utf-8"))
        return True
    except Exception:
        return False


def parse_when(delay_minutes=None, at=None):
    """Return a due time (epoch seconds), or None if it cannot be parsed."""
    now = time.time()
    if delay_minutes not in (None, ""):
        try:
            return now + float(delay_minutes) * 60
        except Exception:
            pass
    if at:
        s = str(at).strip().lower()
        try:
            return datetime.datetime.fromisoformat(at).timestamp()       # ISO timestamp
        except Exception:
            pass
        m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", s)            # '5pm', '17:30', '9:00am'
        if m:
            h, mn, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
            if ap == "pm" and h < 12:
                h += 12
            if ap == "am" and h == 12:
                h = 0
            try:
                t = datetime.datetime.now().replace(hour=h, minute=mn, second=0, microsecond=0)
                if t.timestamp() <= now:
                    t += datetime.timedelta(days=1)                       # already passed -> tomorrow
                return t.timestamp()
            except Exception:
                pass
    return None


def add(text, delay_minutes=None, at=None):
    due_ts = parse_when(delay_minutes, at)
    if not text or not due_ts:
        return {"ok": False, "error": "need a reminder and a valid time (delay_minutes or at)"}
    items = _load()
    items.append({"text": str(text)[:300], "due": due_ts, "fired": False, "created": time.time()})
    _save(items)
    return {"ok": True, "when": datetime.datetime.fromtimestamp(due_ts).strftime("%I:%M %p"), "due": due_ts}


def due(grace=3600):
    """Text of one reminder that is now due (and mark it fired), or '' if none. Skips reminders
    more than `grace` seconds overdue so a long-idle Zoe does not surprise him with stale ones."""
    now = time.time()
    items = _load()
    changed, out = False, ""
    for it in items:
        if not it.get("fired") and it.get("due", 0) <= now:
            it["fired"] = True
            changed = True
            if now - it["due"] <= grace:
                out = it.get("text", "")
                break
    if changed:
        _save(items)
    return out


def upcoming():
    now = time.time()
    return [it for it in _load() if not it.get("fired") and it.get("due", 0) > now]


def cancel(which=""):
    """Cancel an upcoming reminder by 1-based index ('1') or a text substring. Returns {ok, cancelled}."""
    items = _load()
    up = [it for it in items if not it.get("fired") and it.get("due", 0) > time.time()]
    w = str(which or "").strip()
    target = None
    if w.isdigit():
        i = int(w) - 1
        if 0 <= i < len(up):
            target = up[i]
    if target is None and w:
        target = next((it for it in up if w.lower() in it.get("text", "").lower()), None)
    if target is None:
        return {"ok": False, "error": "no matching upcoming reminder",
                "upcoming": [it.get("text", "") for it in up]}
    items.remove(target)
    _save(items)
    return {"ok": True, "cancelled": target.get("text", "")}


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "add":
        print(add(sys.argv[2], delay_minutes=(sys.argv[3] if len(sys.argv) > 3 else None)))
    else:
        print({"upcoming": upcoming(), "due_now": due()})
