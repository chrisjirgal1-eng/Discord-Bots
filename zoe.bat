@echo off
REM ZOE: start the full voice assistant.
REM It opens her live HUD, then listens for "Hey Zoe". Say e.g. "Hey Zoe, show me the news"
REM and she pulls it up in your browser and replies out loud. Close this window to stop her.
REM (For the HUD only, with no voice, run: python tools\zoe_server.py)
python "%~dp0tools\zoe_assistant.py"
