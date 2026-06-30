# ZOE UPDATE: one safe step to push your latest code into the installed app and verify it.
# Double-click zoe-update.bat, or run:  powershell -File tools\zoe-update.ps1 [-NoLaunch]
#
# Why this exists: Zoe runs from an INSTALLED copy (AppData\Local\Programs\Zoe), not the source
# folder. Editing source does nothing until it is synced here. This script kills every running Zoe
# (so no stale code or duplicate voices survive), copies the source in, stamps the commit, prints a
# health check, and relaunches. That is the whole fix for "I updated it but it still shows the old one."
param([switch]$NoLaunch)

$src = "C:\Users\chris\Documents\Discord-Bots"
$dst = "C:\Users\chris\AppData\Local\Programs\Zoe\resources\app"
$exe = "C:\Users\chris\AppData\Local\Programs\Zoe\Zoe.exe"

Write-Host "`n=== ZOE UPDATE ===" -ForegroundColor Cyan

Write-Host "[1/4] stopping every Zoe (installed app, source, voice, backend)..."
Stop-Process -Name Zoe -Force -ErrorAction SilentlyContinue
foreach ($p in @(Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -eq 'electron.exe' -and $_.CommandLine -like '*Discord-Bots*') -or
    $_.CommandLine -like '*zoe_realtime*' -or $_.CommandLine -like '*zoe_server.py*' -or
    $_.CommandLine -like '*zoe_assistant*' })) {
  Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 800

Write-Host "[2/4] syncing your code into the installed app..."
if (-not (Test-Path $dst)) { Write-Host "  WARNING: installed app not found at $dst" -ForegroundColor Yellow }
foreach ($d in 'electron','zoe-ui','tools','workspaces') {
  if (Test-Path "$src\$d") { robocopy "$src\$d" "$dst\$d" /E /NFL /NDL /NJH /NJS /NP | Out-Null }
}
Copy-Item "$src\package.json" "$dst\package.json" -Force -ErrorAction SilentlyContinue
Copy-Item "$src\.env" "$dst\.env" -Force -ErrorAction SilentlyContinue
$commit = (git -C $src rev-parse --short HEAD 2>$null)
if ($commit) { Set-Content "$dst\DEPLOYED_COMMIT.txt" -Value $commit -Encoding ascii }

Write-Host "[3/4] health check..."
$dep = if (Test-Path "$dst\DEPLOYED_COMMIT.txt") { (Get-Content "$dst\DEPLOYED_COMMIT.txt" -Raw).Trim() } else { "?" }
$match = if ($dep -eq $commit) { "UP TO DATE" } else { "STALE" }
Write-Host ("  source commit    : $commit")
Write-Host ("  installed commit : $dep  ($match)")
Write-Host ("  OPS tab present  : " + (Test-Path "$dst\zoe-ui\ops.html"))
$stray = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*zoe_realtime*' -or $_.Name -eq 'Zoe.exe' }).Count
Write-Host ("  stray Zoe procs  : $stray  (want 0 before launch)")

if ($NoLaunch) {
  Write-Host "[4/4] launch skipped (-NoLaunch). Open Zoe from the Windows icon when ready."
} else {
  Write-Host "[4/4] launching the updated Zoe..."
  if (Test-Path $exe) { Start-Process $exe } else { Write-Host "  Zoe.exe not found at $exe" -ForegroundColor Yellow }
}
Write-Host "=== DONE ===`n" -ForegroundColor Green
