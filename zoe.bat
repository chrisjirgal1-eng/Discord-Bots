@echo off
REM Zoe desktop app. Opens the HUD window + system tray + always-on "Hey Zoe" voice,
REM and native app/workspace launching. The window hides to the tray when closed;
REM use the tray icon to quit. (Voice-only, no window: python tools\zoe_assistant.py)
cd /d "%~dp0"
npm start
