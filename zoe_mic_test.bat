@echo off
REM Zoe mic check. Double-click to see if your mic is loud enough for Zoe to hear you.
REM Add  --wake  (zoe_mic_test.bat --wake) to say "hey zoe" and test the full trigger.
cd /d "%~dp0"
set PY=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
"%PY%" tools\zoe_mic_test.py %*
echo.
pause
