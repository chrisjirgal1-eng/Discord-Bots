#!/usr/bin/env python3
"""ZOE's eyes and hands on the machine: read files/logs and run commands to actually fix things.

This is what lets her answer "why did that fail" and then fix it, instead of deflecting. read_file
is read-only and safe. run_command runs a shell command in the repo, but refuses anything that
looks destructive (delete, format, shutdown, ...) unless confirmed=true -- the same confirm-first
posture Chris chose for the browser. Every command is returned with its output so she can read the
result and reason about the next step.
"""
import os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX = 6000          # cap output/file text so a huge log doesn't blow up her context

# Substrings that mean "you can't take this back". Refused unless confirmed=true.
_DANGER = ("rm ", "rmdir", "del ", "rd /s", "rd/s", "format ", "mkfs", "diskpart", "fdisk",
           "shutdown", "reg delete", "deltree", ":(){", "remove-item", "rd ", "> /dev",
           "dd if=", "git push --force", "git reset --hard", "drop table", "drop database")


def read_file(path):
    """Read a text file (last MAX chars) so she can look at a log or some code. Read-only."""
    p = os.path.expanduser(os.path.expandvars((path or "").strip().strip('"')))
    if not os.path.isabs(p):
        p = os.path.join(ROOT, p)
    if not os.path.exists(p):
        return {"ok": False, "error": f"no file at {p}"}
    if os.path.isdir(p):
        try:
            return {"ok": True, "path": p, "listing": sorted(os.listdir(p))[:200]}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            data = f.read()
        return {"ok": True, "path": p, "text": data[-MAX:], "truncated": len(data) > MAX}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def run_command(command, confirmed=False):
    """Run a shell command in the repo and return its output. Refuses destructive commands unless
    confirmed=true. Scoped to the repo dir; 120s cap."""
    cmd = (command or "").strip()
    if not cmd:
        return {"ok": False, "error": "no command"}
    if not confirmed and any(d in cmd.lower() for d in _DANGER):
        return {"ok": False, "danger": True,
                "error": "that looks irreversible -- confirm with him (yes/no), then retry with "
                         "confirmed true"}
    try:
        r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=120,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        return {"ok": r.returncode == 0, "code": r.returncode, "output": out[-MAX:] or "(no output)"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "command timed out (120s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _selftest():
    print("read_file(README... or this file):", read_file("tools/zoe_ops.py").get("ok"))
    print("read missing:", read_file("nope_does_not_exist.xyz").get("ok"))
    print("run echo:", run_command("echo hello").get("output"))
    d = run_command("rm -rf /")
    print("danger refused:", (not d.get("ok")) and d.get("danger") is True)
    print("danger w/ confirmed parses:", run_command("echo rm test", confirmed=True).get("ok"))
    print("ops selftest ok")


if __name__ == "__main__":
    _selftest()
