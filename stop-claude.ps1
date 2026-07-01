# stop-claude.ps1 -- Free Claude Code so you can open it yourself. Zoey keeps running.
#
# This is the FAILSAFE off switch. It does not need Zoey, the desktop app, or Claude Code
# to be running or updated -- it is plain Windows PowerShell. Double-click STOP-CLAUDE.bat
# (which runs this), or run this file directly, any time you want Claude Code back.
#
# What it does, in order:
#   1. Kills the Claude desktop app (Claude.exe) and genuine Claude Code CLI processes,
#      matched precisely (the app by name; the CLI by entrypoint). A .claude config path or
#      a claude.ai browser tab is NOT matched; browsers and VS Code are skipped by name.
#   2. Never touches Zoey: this script's own process and its parents are protected.
#   3. Read-only, tells you what relaunches Claude Code (a scheduled task, a Run key, a
#      Startup shortcut) so the loop can be turned off at the source, not just for a moment.
#   4. If a scheduled task is the source, offers a yes/no to disable it (reversible; re-enable
#      it in Task Scheduler, or by re-running your 24/7 launcher, whenever you want).

$ErrorActionPreference = 'SilentlyContinue'
Write-Host ''
Write-Host '  Freeing Claude Code (Zoey stays on)...' -ForegroundColor Cyan

$me = $PID
$all = Get-CimInstance Win32_Process

# Protect this script's own process tree (self + verified ancestors). A real parent is at least
# as old as its child, which guards against Windows PID reuse pointing the walk at a recycled PID.
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

# App by name; CLI by entrypoint (claude-code, \claude.exe/.cmd, \claude\...cli, a bare "claude ").
$rx = '(?i)(claude[-_ ]?code|(^|[\\/ "''])claude\.(exe|cmd)|[\\/]claude[\\/][^"'' ]*cli|(^|[\\/ "''])claude )'
$skip = @('chrome.exe','msedge.exe','firefox.exe','brave.exe','opera.exe','code.exe')
$killed = @(); $nokill = @()
foreach ($p in $all) {
  if ($protect.Contains([int]$p.ProcessId)) { continue }
  $nm = "$($p.Name)"
  $isApp = ($nm -ieq 'Claude.exe')
  $isCli = ($p.CommandLine -and ($p.CommandLine -match $rx) -and (-not ($skip -contains $nm.ToLower())))
  if (-not ($isApp -or $isCli)) { continue }
  try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop; $killed += ('{0} (pid {1})' -f $nm, $p.ProcessId) }
  catch { $nokill += ('{0} (pid {1})' -f $nm, $p.ProcessId) }
}

if ($killed.Count -gt 0) { Write-Host ('  Stopped: ' + ($killed -join ', ')) -ForegroundColor Green }
elseif ($nokill.Count -eq 0) { Write-Host '  Nothing was holding Claude Code.' -ForegroundColor Green }
if ($nokill.Count -gt 0) {
  Write-Host ('  Found but could NOT stop (right-click this file, Run as administrator): ' + ($nokill -join ', ')) -ForegroundColor Yellow
}

# What relaunches it? Read-only scan: scheduled tasks, Run keys, Startup folder.
$respawn = @()
try {
  Get-ScheduledTask | Where-Object { $_.State -ne 'Disabled' } | ForEach-Object {
    $blob = (@($_.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join ' ')
    if ($blob -match $rx) { $respawn += $_ }
  }
} catch {}

$launchers = @()
foreach ($k in 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run') {
  $item = Get-Item $k -ErrorAction SilentlyContinue
  if ($item) { foreach ($n in $item.Property) { $val = "$($item.GetValue($n))"; if ($val -match $rx) { $launchers += ("Run key [$n]: $val") } } }
}
$startupDir = [Environment]::GetFolderPath('Startup')
if ($startupDir) { Get-ChildItem $startupDir -ErrorAction SilentlyContinue | ForEach-Object { if ($_.Name -match '(?i)claude') { $launchers += ("Startup folder: " + $_.Name) } } }

if ($respawn.Count -gt 0) {
  Write-Host ''
  Write-Host '  A scheduled task looks like it relaunches Claude Code:' -ForegroundColor Yellow
  $respawn | ForEach-Object { Write-Host ('    ' + $_.TaskPath + $_.TaskName) }
  $ans = Read-Host '  Disable it so Claude Code stays off until you turn it back on? (y/n)'
  if ($ans -match '^\s*(y|yes)\s*$') {
    $respawn | ForEach-Object {
      try { Disable-ScheduledTask -TaskName $_.TaskName -TaskPath $_.TaskPath | Out-Null
            Write-Host ('    disabled ' + $_.TaskName + '  (re-enable it in Task Scheduler anytime)') -ForegroundColor Green }
      catch { Write-Host ('    could not disable ' + $_.TaskName + ' -- run this file as administrator') -ForegroundColor Yellow }
    }
  } else { Write-Host '  Left the task alone.' }
}
if ($launchers.Count -gt 0) {
  Write-Host ''
  Write-Host '  Other startup entries that mention Claude (not changed -- tell Zoey/Claude if you want them off):' -ForegroundColor Yellow
  $launchers | ForEach-Object { Write-Host ('    ' + $_) }
}

Write-Host ''
Write-Host '  Done. You can open Claude Code now.' -ForegroundColor Cyan
