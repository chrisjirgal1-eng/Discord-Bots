@echo off
REM ZOE launcher: starts the live telemetry server and opens the HUD in your browser.
REM Double-click this file. Close the "ZOE server" window to stop it.
start "ZOE server" python "%~dp0tools\zoe_server.py"
timeout /t 2 /nobreak >nul
start "" http://localhost:7717
