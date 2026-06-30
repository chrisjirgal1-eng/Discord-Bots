@echo off
REM Stop Zoe (kills the background voice assistant only, not other Python).
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*zoe_assistant.py*' -or $_.CommandLine -like '*zoe_realtime.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Zoe stopped.
timeout /t 1 /nobreak >nul
