#!/usr/bin/env python3
"""ZOE's eyes and hands on the machine: read files/logs and run commands to actually fix things.

This is what lets her answer "why did that fail" and then fix it, instead of deflecting. read_file
is read-only and safe. run_command runs a shell command in the repo, but refuses anything that
looks destructive (delete, format, shutdown, ...) unless confirmed=true -- the same confirm-first
posture Chris chose for the browser. Every command is returned with its output so she can read the
result and reason about the next step.

stop_loop is the kill switch for the 24/7 loop: it frees the Claude Code / Claude desktop app so
Chris can open it himself, without stopping Zoe (she keeps listening).
"""
import os, base64, subprocess

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


# PowerShell that frees Claude Code. It kills the Claude desktop app (Claude.exe) plus any process
# whose command line mentions "claude" (the Claude Code CLI and any .bat/.vbs/scheduled wrapper that
# relaunches it, so killing the child doesn't just respawn). It NEVER touches Zoe: her own process
# and its whole parent chain (python -> electron/cmd -> ...) are protected, so she keeps listening.
# Passed base64-encoded (-EncodedCommand) so the "claude" match can't hit this command itself.
_STOP_LOOP_PS = r"""
$me = $PID
$all = Get-CimInstance Win32_Process
$protect = New-Object 'System.Collections.Generic.HashSet[int]'
[void]$protect.Add([int]$me)
$cur = $all | Where-Object { $_.ProcessId -eq $me } | Select-Object -First 1
while ($cur -ne $null) {
  [void]$protect.Add([int]$cur.ProcessId)
  $pp = [int]$cur.ParentProcessId
  if ($pp -le 0) { break }
  $cur = $all | Where-Object { $_.ProcessId -eq $pp } | Select-Object -First 1
}
$targets = $all | Where-Object {
  (-not $protect.Contains([int]$_.ProcessId)) -and (
    ($_.Name -eq 'Claude.exe') -or
    ($_.CommandLine -and ($_.CommandLine -match '(?i)claude'))
  )
}
$killed = @()
foreach ($t in $targets) {
  try {
    Stop-Process -Id $t.ProcessId -Force -ErrorAction Stop
    $killed += ('{0} (pid {1})' -f $t.Name, $t.ProcessId)
  } catch {}
}
if ($killed.Count -gt 0) { 'KILLED ' + ($killed -join '; ') } else { 'NONE' }
"""


def stop_loop():
    """Turn off the 24/7 loop: kill the Claude Code / Claude desktop app (and any wrapper relaunching
    it) so the app's file lock frees and Chris can open Claude Code himself. Protects Zoe's own
    process tree, so she keeps listening. Windows-only; returns what it stopped."""
    enc = base64.b64encode(_STOP_LOOP_PS.encode("utf-16-le")).decode()
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
                           capture_output=True, text=True, timeout=30,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        if out.startswith("KILLED"):
            stopped = out[len("KILLED"):].strip()
            return {"ok": True, "stopped": stopped,
                    "say": f"Stopped {stopped}. Claude Code is free to open now."}
        if out == "NONE":
            return {"ok": True, "stopped": "",
                    "say": "Nothing was holding Claude Code. It should open fine now."}
        return {"ok": bool(r.returncode == 0), "output": out[-MAX:] or "(no output)"}
    except FileNotFoundError:
        return {"ok": False, "error": "powershell not found (stop_loop is Windows-only)"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "stop_loop timed out (30s)"}
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
