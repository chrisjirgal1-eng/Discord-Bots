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


def add(text, delay_minutes=None, at=None, repeat=None):
    due_ts = parse_when(delay_minutes, at)
    if not text or not due_ts:
        return {"ok": False, "error": "need a reminder and a valid time (delay_minutes or at)"}
    rep = repeat if repeat in ("hourly", "daily", "weekly") else None
    items = _load()
    items.append({"text": str(text)[:300], "due": due_ts, "fired": False,
                  "repeat": rep, "created": time.time()})
    _save(items)
    w = datetime.datetime.fromtimestamp(due_ts).strftime("%I:%M %p")
    return {"ok": True, "when": w + (f" ({rep})" if rep else ""), "due": due_ts}


def due(grace=3600):
    """Text of one reminder that is now due (and mark it fired), or '' if none. Skips reminders
    more than `grace` seconds overdue so a long-idle Zoe does not surprise him with stale ones."""
    now = time.time()
    items = _load()
    changed, out = False, ""
    for it in items:
        if not it.get("fired") and it.get("due", 0) <= now:
            overdue = now - it["due"]
            rep = it.get("repeat")
            if rep in ("hourly", "daily", "weekly"):
                step = {"hourly": 3600, "daily": 86400, "weekly": 604800}[rep]
                nd = it["due"]
                while nd <= now:
                    nd += step                       # reschedule to next future occurrence; stays active
                it["due"] = nd
            else:
                it["fired"] = True
            changed = True
            if overdue <= grace:
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


def snooze(which="", delay_minutes=10, at=None):
    """Push a reminder to a new time. Matches an upcoming OR just-fired (within an hour) reminder by
    1-based index, text, or -- if no `which` -- the most recent one. Returns {ok, text, when}."""
    items = _load()
    now = time.time()
    cands = [it for it in items if (not it.get("fired") and it.get("due", 0) > now)
             or (it.get("fired") and now - it.get("due", 0) <= 3600)]
    w = str(which or "").strip()
    target = None
    if w.isdigit():
        i = int(w) - 1
        if 0 <= i < len(cands):
            target = cands[i]
    if target is None:
        target = next((it for it in cands if w and w.lower() in it.get("text", "").lower()), None)
    if target is None and not w and cands:
        target = cands[-1]
    if target is None:
        return {"ok": False, "error": "no reminder to snooze"}
    new_due = parse_when(delay_minutes if at is None else None, at) or (now + 600)
    target["due"], target["fired"] = new_due, False
    _save(items)
    return {"ok": True, "text": target.get("text", ""),
            "when": datetime.datetime.fromtimestamp(new_due).strftime("%I:%M %p")}


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "add":
        print(add(sys.argv[2], delay_minutes=(sys.argv[3] if len(sys.argv) > 3 else None)))
    else:
        print({"upcoming": upcoming(), "due_now": due()})
