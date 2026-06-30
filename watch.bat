@echo off
REM One-click: download + transcribe every video in tools\video-urls.txt into transcripts\.
REM Needs GROQ_API_KEY or OPENAI_API_KEY in .env (your OpenAI key works). Instagram login-walls
REM most reels, so export a cookies.txt (the "Get cookies.txt LOCALLY" Chrome extension, on an
REM instagram.com tab while logged in) into THIS folder and it's picked up automatically.
cd /d "%~dp0"
set PY=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe
if not exist "%PY%" set PY=python
set COOKIESARG=
if exist "cookies.txt" set COOKIESARG=cookies.txt
"%PY%" -u tools\watch_batch.py tools\video-urls.txt transcripts %COOKIESARG%
echo.
pause
