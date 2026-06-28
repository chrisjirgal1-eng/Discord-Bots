# Handoff: autonomous JARVIS build (resume here)

This file is the runbook for a resumed session (scheduled or manual). Read it first, do the
NEXT undone item with full discipline, then update this file. Chris is away until July 5, 2026.
He authorized continuing the build across sessions. The model resets each run; this file carries.

## Goal

Evolve the JARVIS setup toward the goal-video target (Claude agentic OS: persistent graph
memory, autonomous loops, voice, synthesis to the next move) by doing only SAFE, INTERNAL,
VERIFIED work. Drain the backlog below, then park. Done condition: backlog empty or every
remaining item is blocked on Chris's credentials.

## Hard guardrails (no human is watching, so these are strict)

- Reversible and internal only: code, docs, tests, skills, local installs, commits.
- NEVER do outward-facing or credentialed work: no real emails, no public posts, no deploys to
  prod, no creating or guessing API keys, no spending money, no touching Chris's browser or his
  personal `.claude` settings. If an item needs any of those, mark it BLOCKED and move on.
- One item per run. Verify with a fresh subagent (verification.md) before committing. Run the
  test suite (`python -m pytest -q`, 53 tests) when code changes. Scan banned words/em dashes.
- Branch off the default (`claude/vibrant-cray-tui7og`) per item, merge, push. Commit each step.
- Budget per run: stop after one backlog item plus its verification. Do not loop further.
- Do NOT invent work or refactor working code for its own sake (coding-discipline.md). When the
  backlog is drained, write "BACKLOG DRAINED, waiting on Chris" here and STOP.

## State now (2026-06-27, pushed to default)

65 videos transcribed + TECHNIQUES.md. 4 Devin branches merged (53 tests pass). 9 skills incl.
jarvis + content-pipeline. graphify live (400-node graph). 154 VoltAgents installed. JARVIS.md
map honest about wired vs gated. Everything committed and pushed.

## Backlog (do the top undone item, mark it done with a date)

1. [x] DONE 2026-06-27. Security + quality audit. Bot/Python clean (already verified in the Devin
   merge, 53 tests pass). Website had real findings, flagged not auto-changed (they alter the live
   deployed site, Chris's call): see clearcoatco-website/SECURITY-NOTES.md (public log_job write +
   client-side admin password; reviews auto-publish; stats computed over unfiltered rows; GET writes;
   raw error leakage). A fresh reviewer verified the findings and caught a missed stat-poisoning
   issue, which was added. No source behavior changed.
2. [x] DONE 2026-06-27. Added tests/test_utils.py (23 tests: format_duration, is_script_url_configured,
   require_playing_or_paused, require_voice_client, ensure_voice_connection connect/move/idle paths)
   and tests/test_watch_batch.py (vid_id parsing). Suite now 76 green. A fresh reviewer claimed the
   async tests were vacuous (missing the asyncio marker); verified empirically with a planted failing
   assertion, which DID fail, proving asyncio_mode=auto runs them. Reviewer was wrong; tests are real.
3. [x] DONE 2026-06-27. Added root README.md (the bot, JARVIS, the memory bank, tooling, the
   Clearcoat site, a layout map). Verified every referenced path exists and the 76-test claim is
   accurate (Type-A self-check). The banned-word scan caught em dashes in the first draft; all fixed.
4. [x] DONE 2026-06-27. Wrote memory-bank/jarvis-voice-spec.md (the voice loop: mic to Deepgram to
   `claude -p "jarvis, ..."` to 11 Labs to speaker, the keys, deps, activation steps) and an inert
   CI template `.github/workflows/jarvis-ci.yml.disabled` (runs the 76 tests; the .disabled suffix
   keeps GitHub from firing it; rename to enable). YAML validated. Cross-linked the voice spec in
   JARVIS.md. No secrets, nothing auto-fires.
5. [x] DONE 2026-06-27. All 10 VoltAgent bundles loaded and registered (164 agent files: core-dev 12,
   lang 31, infra 17, qa-sec 18, data-ai 14, dev-exp 16, domains 15, biz 17, meta 12, research 12).
   Noted coverage and the high-value agents for Chris in tools.md, plus the correction that the
   canonical marketplace-add works locally (only the cloud session needs the tarball workaround).
6. [ ] When 1-5 are done or all remaining are BLOCKED: write "BACKLOG DRAINED, waiting on Chris"
   below, list exactly what Chris must provide (voice keys, host secrets, auto-post approval), stop.

## Tried and failed (do not repeat)

- yt-dlp cannot read Chrome/Edge app-bound cookies; external COM decrypt is refused. Use a browser
  cookie-export extension (cookies.txt) or Firefox. Cookie file stays out of the repo.
- Native Windows Python cannot open Git Bash `/c/...` paths; use `C:/...` or the Read tool.

## Backlog Phase B: make JARVIS video-grade (Chris's direction)

Chris wants JARVIS to look and work like the high-production video demos. UI revamp DONE
(jarvis-ui/index.html, neural bg + agent team + activity + voice waveform, ui-designer critique
applied). Remaining, ordered easiest to hardest. Same guardrails: internal/verified only.

- [x] B1 DONE 2026-06-27. Theme switcher in the header: Arc cyan, Zenthra purple, Clearcoat ice,
  Stark gold. Refactored the accent to a single --acc/--acc2 RGB variable so every element including
  the neural-net canvas recolors live. Verified: 0 hardcoded accents left, balanced braces, clean scan.
- [x] B2 DONE 2026-06-27. Added jarvis.bat at the repo root: double-click to open the command center
  UI in the default browser.
- [ ] B3 (medium). Make the agent team real: split the content-pipeline stages (scout, hook, topic,
  script) into discrete sub-skills the orchestrator calls, matching the UI roster and DZ_xzicxQPx.
- [ ] B4 (medium). Status generator: a script that reads the repo (skill count, test count, graph
  nodes) and writes the UI CONFIG status block, so the HUD is always accurate. Run it, verify.
- [x] B5 DONE 2026-06-28. Full two-way VOICE is LIVE. tools/jarvis_voice.py: mic -> Deepgram (hear)
  -> Groq llama-3.3-70b as JARVIS (think) -> ElevenLabs Lily (speak). All three keys in .env, each
  leg verified (Deepgram transcribed the test clip; Groq+TTS answered aloud). tools/jarvis_speak.py
  is the talk-back-only engine. Optional later: ElevenLabs Creator upgrade for the original voice pick.
- [ ] B6 (hard, gated). 24/7: rename the CI template to enable; nightly jobs need secrets + a host.
- [ ] B7 (hard, gated). Live connector data in the HUD (real bookings, guild activity): needs creds.
- [x] B8 DONE 2026-06-28. Renamed the assistant to ZOE and built a live Rainmeter/Iron-Man HUD:
  zoe-ui/index.html (arc reactor, gauges, live graphs, wireframe globe) fed by tools/zoe_server.py
  (real CPU/RAM/disk/network via psutil at localhost:7717). zoe.bat launches it. Voice persona is Zoe.
- [x] B9 DONE 2026-06-28. Zoe now ACTS, not just talks: tools/zoe_assistant.py is a wake-word
  assistant ("Hey Zoe ...") that boots the HUD, hears via Deepgram, routes intent via Groq, and OPENS
  what you ask in the browser (news, youtube, search, sites) while speaking a confirmation. zoe.bat
  runs it. Intent router verified on sample commands; mic/wake VAD needs a live test (RMS_THRESHOLD tunable).
- [x] B10 DONE 2026-06-28. Zoe auto-starts at login, hidden, no command: tools/zoe_autostart.vbs
  (runs the assistant via the pythoncore pythonw with no console) plus a Startup-folder shortcut
  Zoe.lnk. zoe_stop.bat stops her. Note: bare python/pythonw on PATH is the WindowsApps stub without
  the packages, so the launcher must use the full LOCALAPPDATA pythoncore path (it does).
- [x] B11 DONE 2026-06-28. Converted the web app into an Electron desktop app (package.json, electron/).
  Wraps the existing HUD (loads the Python telemetry server) in a secure shell (contextIsolation on,
  nodeIntegration off, sandbox, preload bridge). Native modules: launcher.js (apps/exe/bat/ps1/cmd/
  folders/urls), workspaceManager.js (reads workspaces/<Name>/workspace.json, matches aliases, runs
  in order with delays). System tray, minimize-to-tray, launch-on-startup, global shortcuts
  (push-to-talk Ctrl+Shift+Space), notifications. A localhost control endpoint (7766) lets the voice
  assistant trigger native actions, and the Electron app auto-starts the voice on boot. Example
  workspaces Coding/School/Gaming/Editing + electron/config/apps.json. zoe.bat -> npm start; the
  Startup VBS now launches Electron. electron-builder + electron-updater configured (publish URL is a
  placeholder). Booted cleanly in a smoke test (control server responded, no errors). Run npm install
  first. Live verify: window render, mic wake, and actual app launching need Chris to run it.
- [x] B12 DONE 2026-06-28. Integration check + stabilization (not a rebuild). Centralized ALL command
  routing into tools/zoe_router.py (one place: classify via Groq + execute); zoe_assistant.py now only
  does audio and calls the router. Added the close-app action (launcher.closeApp via taskkill, wired
  through the control endpoint). HUD shows backend status (LIVE / OFFLINE / ERROR) with a warning banner
  and start instructions, and never freezes. Wrote COMMAND_SYSTEM_GUIDE.md documenting the REAL
  architecture (zoe_server.py is the telemetry server, not the command engine), every command, and how
  to add commands safely. Verified: router classify incl close; control endpoint close/launch handled
  live (a leftover Electron instance can shadow a new one via the single-instance lock, kill all first).
- [x] B13 DONE 2026-06-28. Persistent continuity via memory/zoe_state.json (ADDITIVE; existing logic
  unchanged). New tools/zoe_state.py is the single writer (load/save/record_command/set_mode, atomic,
  best-effort with safe defaults). Hooked in: zoe_router.handle() records each command (the state-update
  step) with the handled flag; zoe_assistant restores on startup, sets mode online/offline, saves on
  shutdown; Electron reads it for restore and exposes window.zoe.getState(). Stores session context,
  last commands, workspace state, preferences, system mode. memory/zoe_state.json is gitignored. State
  I/O never blocks the pipeline. Verified: load defaults, record persists, handle() writes, Electron boots.

## Phase C: versioned compatibility kernel (Chris's bootstrap-kernel spec)

Goal: make ZOE forever-compatible and extensible without breaking anything that works. ALL of it
is additive; the 76-test suite still passes and every legacy state field is preserved + mirrored.

- [x] K1 DONE 2026-06-28. Versioned kernel. New tools/zoe_versions.py is the single home of all
  versions (core / command schema / plugin API / state schema, all 1.0.0) with compatible() by
  major version (mismatch -> fallback, never crash). zoe_router.py gained the locked command schema
  (make_command / validate_command -- 8 core keys, unknown fields tucked into payload._extra) and
  route(command, ctrl, simulate) -- the ONE structured entry any source uses, returning
  {handled, fallback, result, trace_id, ...}, never raising. Added a plugin system: /plugins/*.py
  with a versioned contract, load_plugins() that scans + validates + isolates broken plugins, routed
  by name; references plugins/example_plugin.py (echo) + clock_plugin.py (time). State schema bumped
  to a locked v1.0.0 (schema_version/session.mode+workspace+last_active+trace_log/history FIFO cap 50/
  plugins) additively -- legacy keys kept and mirrored so the HUD + the spawned HUD task still read
  workspace_state.last and last_commands. New tools/zoe_diagnostics.py: 6 test groups (state, router,
  UI command, persistence, plugin, backend), PASS/FAIL + health score 0-100, runs on a temp state
  file, never crashes. Verified: diagnostics 15/15 = 100/100; pytest 76 green; legacy + new state
  fields both present. Docs: COMMAND_SYSTEM_GUIDE.md sections 11-14. classify/execute/handle and the
  voice loop untouched. Note: route() is the structured path; the Electron IPC/control endpoints
  remain the execution layer the router calls (UI->router full rewire is a later, larger step).

- [x] K2 DONE 2026-06-28. Wake-word window summon ("hey zoe pops it up"). zoe_assistant.summon_ui()
  POSTs to a new Electron control route /wake (alias /show) the instant a wake word is heard;
  main.js showWindow() now restores + always-on-top-bumps + focuses so the window reliably comes to
  the foreground on Windows. Best-effort: standalone (no Electron) it is a noop. Verified live:
  POST /wake and /show both return {handled:true,shown:true}, app boots clean. Still needs Chris to
  confirm the mic actually triggers the wake on his hardware (no microphone in the build environment).

- [x] K3 DONE 2026-06-28. "Open Zoe by voice" = auto-start hidden + always listening (Chris chose
  this). main.js: --hidden / ZOE_START_HIDDEN starts the window in the tray (ready-to-show skips
  show()), shows a "Zoe is listening, say hey zoe" notification, sets AppUserModelId so Windows
  attributes it to Zoe. zoe_autostart.vbs now passes --hidden. New tools/zoe_install_autostart.ps1
  creates/removes the Startup-folder shortcut (Zoe.lnk -> wscript zoe_autostart.vbs). ENABLED it for
  Chris (shortcut verified in Startup). Flow: login -> Zoe boots hidden, listens -> "hey zoe" hits
  /wake -> window pops. Verified: hidden boot leaves control endpoint live + /wake returns
  {handled:true,shown:true}, no errors. Real-mic trigger still needs Chris to confirm on his hardware.

- [x] K4 DONE 2026-06-28. Zoe's voice was too quiet. jarvis_speak.play() now maximizes loudness in
  the ffmpeg step: speechnorm pushes speech to the ceiling + alimiter prevents clipping, with a
  ZOE_VOICE_GAIN env knob (default +4 dB; raise for louder, negative to back off). Falls back to a
  plain convert if the build lacks the filters, so playback never breaks. Measured on a real clip:
  mean -21.4 -> -11.8 dB (+9.6 dB, ~2x perceived), peak -5 -> 0 dB (maxed). Note: this maxes the
  SIGNAL; if Chris still cannot hear it, the Windows system/speaker volume is the remaining factor.

- [x] K5 DONE 2026-06-28. Make Zoe actually hear you (hands-free wake). zoe_assistant now
  auto-calibrates the mic threshold at startup: calibrate_threshold() samples ~1.2s of room noise
  and sets the wake bar to ambient x2.5, bounded [250,1500], overridable by ZOE_MIC_THRESHOLD in
  .env (replaces the blind hardcoded 600). New tools/zoe_mic_test.py (+ zoe_mic_test.bat): a live
  RMS meter showing your voice vs the wake line with a suggested threshold, and --wake to record
  "hey zoe" -> Deepgram -> confirm the trigger. Verified: calibrate returns a safe int even with no
  mic (got 469 here from a real ambient sample), env override honored, compiles. The full
  speak-into-mic -> wake -> window-pop loop still needs Chris to run on his hardware (no mic in CI).

- [x] K6 DONE 2026-06-28. Packaged Zoe into a real desktop app (no terminal). package.json build
  fixed: asar:false (so bundled tools/ + zoe-ui/ stay on disk for Python; ROOT=__dirname/.. works
  packaged), nsis per-user (oneClick:false, perMachine:false, desktop+startmenu shortcuts), .env
  bundled so it runs out of the box. main.js: background services spawn via pythonwExe() (windowless)
  with windowsHide:true so no console flashes; login auto-start passes --hidden (tray toggle + IPC +
  startup line). launcher.js taskkill gets windowsHide. Built successfully: dist/Zoe Setup 0.1.0.exe
  (78.5 MB installer) + dist/win-unpacked/Zoe.exe (180 MB). Smoke-tested the PACKAGED exe: telemetry
  7717/stats served live data and control 7766/wake returned handled -- proves pythonw + packaged
  paths work. Build gotcha: electron-builder's winCodeSign extraction fails on macOS .dylib symlinks
  without Windows Developer Mode; worked around by pre-extracting winCodeSign-2.6.0 into the
  electron-builder cache (the 2 darwin symlinks are irrelevant to Windows). Unsigned (no cert).
  Caveat: bundled .env contains API keys -> the installer is private, do not share it.

- [x] K7 DONE 2026-06-28. Command bar (Spotlight/Raycast-style palette) + explainable actions,
  sharing ONE engine with voice. New zoe_router.process(text, source, ...) is the shared pipeline:
  classify -> _explain (parsed intent + steps) -> execute -> record; returns a rich explainable
  result. handle() (voice) now delegates to process(), so voice + typed use the same engine (no
  duplicate logic). New tools/zoe_cli.py: typed text -> process() -> one JSON line (the bridge the
  bar spawns). Electron: createPalette() (frameless/transparent/always-on-top, secure preload
  palette-preload.js exposing window.zoeBar), palette.html (dark UI: input, animated step preview,
  status, result, Reasoning toggle, History panel reading state). Ctrl+Space toggles it; hides on
  blur/Esc. IPC command:run -> runCommandText() spawns python tools/zoe_cli.py (windowsHide). record_
  command now stores a summary for the history panel. Verified: zoe_cli emits correct parsed/steps
  JSON; node --check + palette JS balanced; diagnostics still 100/100; app boots with the palette,
  control endpoint live, no errors. The Ctrl+Space keypress + live UI is the user's to try. Vanilla
  JS (not React) on purpose -- matches the existing secure no-build-step renderer; COMMAND_SYSTEM_GUIDE
  section 15.

- [x] K8 DONE 2026-06-28. Fixed "voice does not open Zoe / backend offline". Root cause: the
  Python services (telemetry + voice) were spawned with stdio:'ignore', so when they failed in a
  build they failed INVISIBLY; the installed app the user ran had no Python side at all. Confirmed
  the latest dev code starts everything (7717 + 7766 up, pythonw zoe_assistant.py running, voice log
  shows "ZOE is listening", threshold 1911). Hardening in main.js: (1) pythonwExe() now falls back to
  the pythoncore python.exe if pythonw.exe is absent, never to the packageless WindowsApps stub;
  (2) openLog() captures each service's output to %APPDATA%\<app>\zoe-telemetry.log / zoe-voice.log;
  (3) spawn Python with -u so those logs are live (block-buffering kept them empty); (4)
  killStrayServices() runs at startup to kill orphaned voice/telemetry from a crashed run so multiple
  listeners never fight the mic; startup re-timed (killStray -> telemetry@800ms -> window@1500ms ->
  voice@2600ms) so the kill snapshot never catches the fresh services. NOTE: the installer (Zoe Setup
  0.1.0.exe) predates all of K6.5-K8; it must be rebuilt (npm run dist) for the installed app to get
  the command bar, hotkey, and these fixes. For now run zoe.bat (verified working). Mic threshold 1911
  may be too high for normal speaking volume; lower ZOE_MIC_THRESHOLD in .env if she misses you.

- [x] K9 DONE 2026-06-28. Obsidian memory + 3D Command Center (4-part request). (1) Scanned: no
  vault existed; memory was zoe_state.json + memory-bank/*.md + ~/.claude MEMORY.md. (2) Built
  tools/zoe_memory.py = an Obsidian-compatible markdown vault (vault/): write/read/search/sync/
  resume/log_command, best-effort. sync() snapshots zoe_state into a dated session note; resume()
  returns last session + state; auto index.md with [[wikilinks]]. (3) zoe_router: new 'memory'
  action (recall/'what did I say last session') through the same process(); every command logged to
  the vault. zoe_server: GET /memory/read, GET /session/resume, POST /memory/write, POST /memory/sync,
  POST /command (runs process()), + load_env() for the Groq key; serves /3d. zoe_assistant syncs on
  shutdown. (4) zoe-ui/os3d.html: real Three.js 3D HUD (PBR orb + glow + rings, depth particle field,
  soft purple/cyan lights, parallax camera) with CSS3D glass panels (memory timeline, live processes,
  command console) wired to /stats + /session/resume + /command; degrades to a fallback without WebGL/
  CDN. main.js: openCommandCenter() window + tray '3D Command Center'. vault/ committed (README +
  notes/), runtime (sessions/, log/, index.md) gitignored. Verified: all endpoints live, recall works,
  /3d serves, diagnostics 100/100. The 3D UI is a strong v1 foundation (Three.js from CDN, needs net).

## Next step

B3 (split the content-pipeline stages into real sub-skills matching the UI roster). Branch:
claude/vibrant-cray-tui7og. When B3 to B4 are done, only the gated items (B5 to B7) remain; park
and wait on Chris for keys, a host, and approvals.
