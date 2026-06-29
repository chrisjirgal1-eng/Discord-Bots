@echo off
REM ZOE speech-to-speech mode. Double-click to launch the OpenAI Realtime voice agent.
REM Needs OPENAI_API_KEY in .env. Say "Hey Zoe" to wake her; she idles free until then.
REM First run only: install deps once with  pip install -r tools\requirements.txt
cd /d "%~dp0"
set PY=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
"%PY%" tools\zoe_realtime.py %*
echo.
pause
