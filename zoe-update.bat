@echo off
REM Double-click this to update the installed Zoe to your latest code, verify it, and relaunch.
REM It kills any running Zoe first, so no stale code or duplicate voices survive.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\zoe-update.ps1" %*
echo.
pause
