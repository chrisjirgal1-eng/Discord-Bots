# Zoe Command System Guide

How Zoe is wired, how a spoken command becomes an action, and how to add new commands
safely. Read this before changing the command logic.

## 1. The real architecture (read this first)

A common misconception: "zoe_server.py is the backend command engine." It is not.
`zoe_server.py` is only the **telemetry server** that serves the HUD and live system stats.
The pieces are:

| Component | File | Role | Port |
|---|---|---|---|
| HUD (UI) | `zoe-ui/index.html` | The visual interface (reactor, gauges, live graphs) | served on 7717 |
| Telemetry server | `tools/zoe_server.py` | Real CPU/RAM/disk/net via psutil; serves the HUD | 7717 |
| Voice I/O | `tools/zoe_assistant.py` | Ears, mouth, wake word. Captures audio, transcribes, speaks | n/a |
| Command router | `tools/zoe_router.py` | The ONE place a phrase becomes an action | n/a |
| Desktop shell | `electron/main.js` | Window, tray, shortcuts, IPC, native execution + control endpoint | 7766 |
| Native services | `electron/services/launcher.js`, `workspaceManager.js` | Actually launch/close apps, open folders, run workspaces | n/a |

Data flow for a voice command:

```
mic -> zoe_assistant.py (STT via Deepgram) -> zoe_router.py (classify via Groq)
     -> zoe_router.execute() -> POST http://127.0.0.1:7766 (Electron control endpoint)
     -> launcher.js / workspaceManager.js (open app, open folder, run workspace)
     -> zoe_assistant.py speaks the reply (ElevenLabs)
```

For UI clicks, the renderer calls `window.zoe.*` (preload) -> IPC -> the same native services.
So there is one set of native execution primitives (Electron), reached two ways: the control
endpoint (for voice) and IPC (for the UI).

## 2. Processes: what to start, how, and what they need

- **Telemetry server (required for live stats and to serve the HUD)**
  - Start: `python tools/zoe_server.py`
  - Port: `http://localhost:7717` (HUD at `/`, stats at `/stats`)
  - Needs: `psutil` (`pip install -r tools/requirements.txt`)
  - The Electron app starts this automatically. Standalone, `zoe_assistant.py` starts it too.

- **Voice assistant (the command engine front end)**
  - Start: `python tools/zoe_assistant.py`
  - Needs: `.env` keys `GROQ_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`,
    plus `sounddevice`, `numpy`. Reads `ZOE_CONTROL` (set by Electron) to reach the control endpoint.

- **Desktop app (everything together)**
  - Start: `npm start` (or `zoe.bat`). Auto-starts at login via `tools/zoe_autostart.vbs`.
  - It spawns the telemetry server, opens the HUD, starts the control endpoint on 7766, and
    starts the voice assistant.

## 3. Backend status in the UI (running / disconnected / error)

The HUD polls `/stats` once a second and never blocks the UI:

- **BACKEND LIVE** (green): stats are flowing. Shows "DESKTOP" when running inside Electron.
- **BACKEND OFFLINE** (amber): the telemetry server is unreachable. A banner appears with start
  instructions; the HUD keeps running on a simulated feed.
- **BACKEND ERROR** (red): the server answered but with bad data. Banner shows a restart hint.

The HUD is fully usable in all three states; it degrades, it does not freeze.

## 4. Supported commands

All command meaning is decided in `zoe_router.py` (`classify`) and dispatched in
`zoe_router.py` (`execute`). The action types:

| Action | Example phrases | What happens | Runs in |
|---|---|---|---|
| workspace | "start coding", "developer mode", "start gaming" | Launches every app + site in `workspaces/<Name>/workspace.json`, in order, with delays | Electron `workspaceManager.js` |
| launch | "launch Discord", "open Spotify", "open Notepad" | Opens the app | Electron `launcher.js` (or Python `start` if Electron is off) |
| close | "close Discord", "quit Spotify" | Closes the app by process name | Electron `launcher.js` (`taskkill /im`) |
| folder | "open my Downloads folder", "open Documents" | Opens the folder in Explorer | Electron `launcher.js` (or Python `os.startfile`) |
| web | "show me the news", "search the Lakers score", "play lofi on YouTube" | Opens the best URL in the browser | the browser |
| chat | "how are you", "what can you do" | Just a spoken reply | nothing, voice only |

Voice commands are any of the above, addressed to Zoe. AI commands are the `chat` action (a
spoken Groq reply) and the `web` action (Groq picks the URL).

## 5. How voice commands are parsed

1. `zoe_assistant.py` records an utterance (energy voice-activity detection, `RMS_THRESHOLD`).
2. It transcribes with Deepgram.
3. It checks the transcript for a wake word ("zoe", "hey zoe"). If absent, it ignores the line.
4. It strips the wake word and passes the rest to `zoe_router.handle(command, ...)`.
5. `zoe_router.classify()` asks Groq for a strict JSON action `{action, target, url, say}`.
6. `zoe_router.execute()` dispatches that action (section 1 flow). The `say` line is spoken.

## 6. How open / close apps works internally

- **Open** (`launcher.launchOne`): a target is classified. A URL opens with `shell.openExternal`.
  A path runs by extension (`.exe` spawned, `.bat`/`.cmd` via `cmd /c`, `.ps1` via PowerShell,
  a folder/document via `shell.openPath`). A bare app name is resolved through
  `electron/config/apps.json` (friendly name -> command or full path) and launched with
  Windows `start`. If a name will not resolve, add its path to `apps.json`, no code change.
- **Close** (`launcher.closeApp`): the app name becomes a process image name (Discord -> Discord.exe)
  and is closed with `taskkill /im "<name>.exe" /f`. It only ever kills by image name, never an
  arbitrary command.

## 7. Workspaces

`workspaces/<Name>/workspace.json` defines `name`, `aliases`, `launch` (apps/paths), `websites`,
optional `folders`, `files`, `delayMs`, and `startupScript`. `workspaceManager.match()` maps a
phrase to a workspace by name or alias; `run()` launches `launch` items in order (with `delayMs`
between), then folders, files, and websites. Add a new workspace by creating a new folder with a
`workspace.json`; Zoe discovers it. No code change.

## 8. How to add a new command safely

1. Decide if it fits an existing action (workspace, launch, close, folder, web, chat). If yes,
   just add a workspace JSON or an `apps.json` entry. No code.
2. For a genuinely new action type:
   - Add the action name and its rule to `INTENT_SYS` in `tools/zoe_router.py`.
   - Add an `elif a == "<new>":` branch in `zoe_router.execute()` that POSTs to the control
     endpoint with a new field, or does a safe Python fallback.
   - Add a matching `else if (data.<field>)` branch in the control handler in `electron/main.js`,
     calling a new function in `launcher.js` or `workspaceManager.js`.
   - Keep execution primitives in Electron and routing decisions in `zoe_router.py`. Do not
     scatter command logic into `zoe_assistant.py` (it only does audio).
3. Test the routing without hardware: `classify("your phrase", GROQ_API_KEY)` should return the
   action you expect before you wire execution.

## 9. Debugging

- HUD blank or "BACKEND OFFLINE": start `python tools/zoe_server.py` and check `http://localhost:7717/stats`.
- Voice not reacting: run `python tools/zoe_assistant.py` in a console; if it never prints "heard",
  lower `RMS_THRESHOLD`. If it mishears, raise it.
- A command does nothing: check the printed `intent:` line. If the action is right but nothing
  launches, the app name is unresolved, add it to `electron/config/apps.json`.
- Native actions ignored from voice: confirm Electron is running (the control endpoint on 7766
  must answer); `curl -X POST http://127.0.0.1:7766/action -d '{}'` returns `{"handled":false}`.
