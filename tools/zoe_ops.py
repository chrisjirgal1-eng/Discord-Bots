#!/usr/bin/env python3
"""ZOE's eyes and hands on the machine: read files/logs and run commands to actually fix things.

This is what lets her answer "why did that fail" and then fix it, instead of deflecting. read_file
is read-only and safe. run_command runs a shell command in the repo, but refuses anything that
looks destructive (delete, format, shutdown, ...) unless confirmed=true -- the same confirm-first
posture Chris chose for the browser. Every command is returned with its output so she can read the
result and reason about the next step.

stop_loop is the kill switch for the 24/7 loop: it frees the Claude Code / Claude desktop app so
Chris can open it himself, without stopping Zoe (she keeps listening). It matches the app + CLI
precisely and only reports a scheduled-task respawn source rather than changing his config silently.
"""
import os, json, base64, subprocess

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


# PowerShell that frees Claude Code so Chris can open it himself. It kills the Claude desktop app
# (Claude.exe) and genuine Claude Code CLI processes, matched PRECISELY -- the app by name, the CLI
# by an entrypoint pattern (claude-code, \claude.exe/.cmd, \claude\...cli, a bare "claude " command).
# A bare "claude" substring is deliberately NOT used: it would wrongly kill a claude.ai browser tab,
# an editor open on a .claude path, etc. Zoe's own process and its whole parent chain (python ->
# electron/cmd -> ...) are protected, so she keeps listening. Passed base64 (-EncodedCommand) so the
# match can't hit this command itself. It does NOT stop a respawn source on its own: it only SCANS
# (read-only) for a scheduled task whose action runs Claude Code and reports it, so Zoe can offer to
# disable it with Chris's yes rather than change his config silently. Emits one compact JSON line.
_STOP_LOOP_PS = r"""
$me = $PID
$all = Get-CimInstance Win32_Process
# protect Zoe's own tree: self + verified ancestors (a real parent is at least as old as its child,
# which guards against Windows PID reuse pointing the walk at an unrelated recycled PID)
$protect = New-Object 'System.Collections.Generic.HashSet[int]'
[void]$protect.Add([int]$me)
$cur = $all | Where-Object { $_.ProcessId -eq $me } | Select-Object -First 1
while ($cur -ne $null) {
  [void]$protect.Add([int]$cur.ProcessId)
  $pp = [int]$cur.ParentProcessId
  if ($pp -le 0) { break }
  $parent = $all | Where-Object { $_.ProcessId -eq $pp } | Select-Object -First 1
  if ($parent -eq $null) { break }
  if ($parent.CreationDate -ne $null -and $cur.CreationDate -ne $null -and $parent.CreationDate -gt $cur.CreationDate) { break }
  $cur = $parent
}
$rx = '(?i)(claude[-_ ]?code|(^|[\\/ "''])claude\.(exe|cmd)|[\\/]claude[\\/][^"'' ]*cli|(^|[\\/ "''])claude )'
$skip = @('chrome.exe','msedge.exe','firefox.exe','brave.exe','opera.exe','code.exe')
$killed = @(); $nokill = @()
foreach ($p in $all) {
  if ($protect.Contains([int]$p.ProcessId)) { continue }
  $nm = "$($p.Name)"
  $isApp = ($nm -ieq 'Claude.exe')
  $isCli = ($p.CommandLine -and ($p.CommandLine -match $rx) -and (-not ($skip -contains $nm.ToLower())))
  if (-not ($isApp -or $isCli)) { continue }
  try {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
    $killed += ('{0} (pid {1})' -f $nm, $p.ProcessId)
  } catch {
    $nokill += ('{0} (pid {1})' -f $nm, $p.ProcessId)   # e.g. elevated process, non-elevated Zoe
  }
}
# read-only: is a scheduled task the respawn source? Report it; do not disable (config change).
$respawn = @()
try {
  Get-ScheduledTask -ErrorAction Stop | Where-Object { $_.State -ne 'Disabled' } | ForEach-Object {
    $blob = (@($_.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join ' ')
    if ($blob -match $rx) { $respawn += ($_.TaskPath + $_.TaskName) }
  }
} catch {}
[pscustomobject]@{ killed = $killed; nokill = $nokill; respawn = $respawn } | ConvertTo-Json -Compress
"""


def _as_list(x):
    """ConvertTo-Json renders an empty array as null and a one-item array as a scalar; normalize."""
    if not x:
        return []
    return list(x) if isinstance(x, list) else [x]


def _summarize_stop(killed, nokill, respawn):
    """Pure: turn the kill / couldn't-kill / respawn lists into (ok, spoken line). Cloud-testable.
    ok is True only when nothing was left un-stopped, so Zoe never claims the app is free when a
    process she couldn't kill may still hold the lock."""
    if killed:
        say = "Stopped " + "; ".join(killed) + ". Claude Code is free to open now."
    elif nokill:
        say = ("I found Claude Code (" + "; ".join(nokill) + ") but couldn't stop it, it may be "
               "running as admin. Want me to try again elevated?")
    else:
        say = "Nothing was holding Claude Code, so it should open fine now."
    if respawn:
        say += (" Heads up, a scheduled task (" + "; ".join(respawn) + ") looks like it relaunches "
                "it. Want me to disable that too?")
    return (len(nokill) == 0), say


def stop_loop():
    """Turn off the loop: kill the Claude Code / Claude desktop app so its file lock frees and Chris
    can open Claude Code himself. Protects Zoe's own process tree, so she keeps listening. If a
    scheduled task looks like it relaunches Claude Code, she reports it (does not disable it) so she
    can offer to turn it off with his yes. Windows-only; returns what it stopped."""
    enc = base64.b64encode(_STOP_LOOP_PS.encode("utf-16-le")).decode()
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
                           capture_output=True, text=True, timeout=45,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError:
        return {"ok": False, "error": "powershell not found (stop_loop is Windows-only)"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "stop_loop timed out (45s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    out = (r.stdout or "").strip()          # sentinel is stdout-only; stderr never corrupts parsing
    try:
        data = json.loads(out) if out else {}
    except Exception:
        data = {}
    if not out and r.returncode != 0:
        return {"ok": False, "error": ((r.stderr or "").strip()[:200] or "powershell failed")}
    killed, nokill, respawn = (_as_list(data.get("killed")), _as_list(data.get("nokill")),
                               _as_list(data.get("respawn")))
    ok, say = _summarize_stop(killed, nokill, respawn)
    return {"ok": ok, "killed": killed, "nokill": nokill, "respawn": respawn, "say": say}


def _selftest():
    print("read_file(README... or this file):", read_file("tools/zoe_ops.py").get("ok"))
    print("read missing:", read_file("nope_does_not_exist.xyz").get("ok"))
    print("run echo:", run_command("echo hello").get("output"))
    d = run_command("rm -rf /")
    print("danger refused:", (not d.get("ok")) and d.get("danger") is True)
    print("danger w/ confirmed parses:", run_command("echo rm test", confirmed=True).get("ok"))
    # stop_loop summary logic (pure; the real kill is Windows-only and not run here)
    ok_k, _ = _summarize_stop(["Claude.exe (pid 1)"], [], [])
    ok_n, say_n = _summarize_stop([], ["Claude.exe (pid 2)"], [])
    ok_e, _ = _summarize_stop([], [], [])
    _, say_r = _summarize_stop(["Claude.exe (pid 3)"], [], ["\\jarvis-autobuild"])
    assert ok_k is True and ok_e is True and ok_n is False           # can't-kill => not ok
    assert "admin" in say_n and "relaunches" in say_r                # honest wording
    assert _as_list(None) == [] and _as_list("x") == ["x"] and _as_list(["a", "b"]) == ["a", "b"]
    print("stop_loop summary ok:", ok_k, ok_n, ok_e)
    print("ops selftest ok")


if __name__ == "__main__":
    _selftest()
