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
  - Start: `npm start` (or `zoe.bat`) shows the window. Launch with `--hidden` (or env
    `ZOE_START_HIDDEN=1`) to start in the tray, listening, with no window until summoned.
  - It spawns the telemetry server, opens the HUD, starts the control endpoint on 7766, and
    starts the voice assistant.
  - Auto-start hidden at login: `powershell -File tools/zoe_install_autostart.ps1` creates a
    Startup shortcut that runs `tools/zoe_autostart.vbs` (Electron `--hidden`). Saying "hey zoe"
    then opens the window. Undo with `... -Remove` or the tray's "Launch on startup" toggle.

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
   On a hit it also POSTs to the Electron control route `/wake`, which brings the Zoe window to
   the front (the "hey zoe pops it up" behavior). This is best-effort and only applies under the
   desktop app; standalone, there is no window to summon.
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
- Voice not reacting (Zoe cannot hear you): run `python tools/zoe_mic_test.py` (or double-click
  `zoe_mic_test.bat`) to see your live mic level against the wake line, and `--wake` to say
  "hey zoe" and confirm the full trigger. Zoe auto-calibrates the threshold to the room at startup;
  to pin it, set `ZOE_MIC_THRESHOLD` in `.env` to the value the meter suggests (lower = more
  sensitive). If she mishears the words rather than missing them, that is Deepgram, not the level.
- A command does nothing: check the printed `intent:` line. If the action is right but nothing
  launches, the app name is unresolved, add it to `electron/config/apps.json`.
- Native actions ignored from voice: confirm Electron is running (the control endpoint on 7766
  must answer); `curl -X POST http://127.0.0.1:7766/action -d '{}'` returns `{"handled":false}`.

## 10. Persistent continuity (memory/zoe_state.json)

ZOE survives restarts. `memory/zoe_state.json` holds the session context, the last commands, the
last workspace, preferences, and the system mode. `tools/zoe_state.py` is the SINGLE writer
(load / save / record_command / set_mode), so the Python and Electron processes never race;
Electron only reads it.

- On startup: `zoe_assistant.py` calls `zoe_state.start_session()` (restores prior state, or safe
  defaults if the file is missing or corrupt) and sets the mode online/offline by pinging the
  telemetry server. The Electron app reads the same file for restore.
- On every command: `zoe_router.handle()` calls `zoe_state.record_command(text, action, handled,
  workspace)` as the final "state updated" step of the pipeline.
- On shutdown: the assistant rewrites the file (last_seen).

It is fully best-effort: every state call swallows its own errors, so a missing, locked, or corrupt
file never blocks a command, and ZOE falls back to safe defaults. The renderer can read the state
read-only via `window.zoe.getState()`. The file is generated at runtime and gitignored.

## 11. Versioned kernel (the compatibility contract)

So the system stays compatible forever, all of it is versioned. `tools/zoe_versions.py` is the one
place the versions live (core, command schema, plugin API, state schema -- all 1.0.0 today).

Forward-compatibility law: upgrades are ADDITIVE ONLY, old fields are never removed, unknown
fields are ignored or preserved, and a version MISMATCH degrades to fallback mode, never a crash.
`zoe_versions.compatible(theirs, ours)` decides by MAJOR version; a different major still runs,
just flagged `fallback: true` in the result.

Locked command schema (core keys never change; new fields go inside `payload` only):

```
{ schema_version, source, intent, target, action, payload, timestamp, trace_id }
  source: ui | assistant | voice | system | plugin
  intent: open_app | close_app | navigate | system_action | plugin_action
```

`zoe_router.make_command(...)` builds one; `zoe_router.validate_command(...)` normalizes any input
into it (fills missing core keys, tucks unknown top-level fields into `payload._extra`, never raises).

Locked state schema (section 10) is v1.0.0: `schema_version`, `session`, `history` (FIFO, capped at
`max_entries` = 50), `plugins`. The legacy keys (`system_mode`, `last_commands`, `workspace_state`,
`preferences`) are kept and mirrored so older readers and the HUD keep working.

## 12. route(): the structured command entry

`zoe_router.route(command, ctrl=None, simulate=False)` is the ONE structured entry any source uses
(the voice path still uses `handle()`; both live in the router, so routing stays centralized). It
validates -> maps the intent to execution (or a plugin) -> records state -> returns:

```
{ schema_version, trace_id, source, intent, handled: bool, fallback: bool, result: {...} }
```

It never raises: any internal error returns `handled: false` with a structured error (noop
fallback). `simulate=True` runs the decision without side effects -- used by diagnostics and any
offline/dry-run path. Intent mapping: open_app->launch, close_app->close, navigate->web,
system_action->workspace (or folder if `payload.folder` is set), plugin_action->the named plugin.

## 13. Plugins

`/plugins/*.py` extend ZOE without touching the core. Each exposes a `PLUGIN` metadata dict
(`plugin_name`, `plugin_version`, `schema_version`, `supported_intents`) and an `execute(command)`
returning `{handled, result}`. `zoe_router.load_plugins()` scans the folder at startup, validates
the contract, skips anything incompatible or broken (isolated), and registers the rest. A
`plugin_action` command is routed to the plugin named by its `target`. See `plugins/README.md` and
the references `example_plugin.py` (echo) and `clock_plugin.py` (time).

## 14. Diagnostics

`python tools/zoe_diagnostics.py` runs six test groups (state, router, UI command, persistence,
plugin, backend), prints PASS/FAIL per test, and reports a system health score (0-100) plus a final
validation block. It points the state layer at a temp file (never touches real state) and never
crashes. Exit 0 when every test passes, else 1.

## 15. Command bar (the Spotlight-style palette)

`Ctrl+Space` opens a centered command bar. Typed requests run through the EXACT SAME engine as
voice -- there is one pipeline, `zoe_router.process(text, source, ...)`:

```
voice  : zoe_assistant -> zoe_router.handle() -> process()   (source="voice", speaks the reply)
command: palette.html  -> command:run (IPC)   -> main.runCommandText() -> python tools/zoe_cli.py
                       -> zoe_router.process()                (source="ui",   shows the steps)
```

`process()` returns an explainable result: `{parsed, steps, intent, target, url, handled, status,
say, trace_id}`. The palette renders it as an Action Preview -- the parsed intent, the step list
revealed one by one, a live status, then the result. A **Reasoning** toggle shows every decision
(intent, target, url, handled, trace id); a **History** panel reads `history.last_commands` from
the state file, each entry expandable to its parsed summary. The palette is a frameless,
transparent, always-on-top window (`electron/palette.html` + `electron/palette-preload.js`), same
secure posture as the HUD (contextIsolation on, nodeIntegration off, one allow-listed bridge
`window.zoeBar`). It hides on blur or Esc. Because both front ends call `process()`, there is no
duplicate command logic -- adding an action type (section 8) lights it up for voice and the bar at once.
