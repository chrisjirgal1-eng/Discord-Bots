# Enable (or remove) Zoe auto-start at login. Creates a Startup-folder shortcut that runs
# tools\zoe_autostart.vbs, which launches the Electron app HIDDEN (--hidden) so Zoe listens in
# the tray and "hey zoe" opens it. This is the only system-level change Zoe makes; undo it any
# time with  -Remove  or by unchecking "Launch on startup" in the tray.
#
#   powershell -ExecutionPolicy Bypass -File tools\zoe_install_autostart.ps1
#   powershell -ExecutionPolicy Bypass -File tools\zoe_install_autostart.ps1 -Remove
param([switch]$Remove)
$ErrorActionPreference = 'Stop'

$root    = Split-Path -Parent $PSScriptRoot          # repo root (tools\..)
$vbs     = Join-Path $root 'tools\zoe_autostart.vbs'
$startup = [Environment]::GetFolderPath('Startup')
$lnk     = Join-Path $startup 'Zoe.lnk'

if ($Remove) {
  if (Test-Path $lnk) { Remove-Item $lnk -Force; Write-Host "Zoe auto-start removed: $lnk" }
  else { Write-Host "No Zoe auto-start shortcut found." }
  return
}

if (-not (Test-Path $vbs)) { throw "Cannot find $vbs" }

$sh = New-Object -ComObject WScript.Shell
$s  = $sh.CreateShortcut($lnk)
$s.TargetPath       = Join-Path $env:WINDIR 'System32\wscript.exe'
$s.Arguments        = '"' + $vbs + '"'
$s.WorkingDirectory = $root
$s.WindowStyle      = 7                               # minimized / no flash
$s.Description      = 'Start Zoe hidden at login (always listening)'
$s.Save()
Write-Host "Zoe auto-start ENABLED (hidden). Shortcut: $lnk"
Write-Host 'Zoe will start in the tray at next login. Say "hey zoe" to open it.'
