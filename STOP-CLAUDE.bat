@echo off
title Free Claude Code (Zoey stays on)
REM ==========================================================================
REM  Double-click this to STOP Claude Code so you can open it yourself.
REM  Zoey keeps running -- this only frees Claude Code, it does not touch her.
REM
REM  This is your failsafe: it needs nothing updated, no Zoey, no Claude Code.
REM  Keep a copy on your Desktop. The readable logic is in stop-claude.ps1
REM  (same folder). If a scheduled task relaunches Claude Code, it will ask
REM  you yes/no to turn that off.
REM ==========================================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-claude.ps1"
echo.
pause
