'use strict';
// Zoe desktop, main process. Wraps the existing Zoe HUD (served by the Python telemetry
// server) in a secure Electron shell and adds native desktop power: app launching,
// workspaces, tray, global shortcuts, native notifications, and a local control endpoint
// the voice assistant uses to run desktop actions.

const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain, shell, Notification, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const ROOT = path.join(__dirname, '..');
const WorkspaceManager = require('./services/workspaceManager');
const launcher = require('./services/launcher');
const wsm = new WorkspaceManager(path.join(ROOT, 'workspaces'), path.join(__dirname, 'config'));

const TELEMETRY_PORT = 7717;
const CONTROL_PORT = 7766;
let win = null, tray = null, telemetryProc = null, voiceProc = null, controlServer = null;

// ---- python resolution (the bare `python` on PATH is the Windows Store stub) ----
function pythonExe() {
  const local = process.env.LOCALAPPDATA &&
    path.join(process.env.LOCALAPPDATA, 'Python', 'pythoncore-3.14-64', 'python.exe');
  if (local && fs.existsSync(local)) return local;
  return 'python';
}

// ---- tray / window icon ----
function icon() {
  const p = path.join(__dirname, 'assets', 'zoe.png');
  return fs.existsSync(p) ? nativeImage.createFromPath(p) : nativeImage.createEmpty();
}

// ---- start the Python telemetry server so the HUD has live data ----
function startTelemetry() {
  try {
    telemetryProc = spawn(pythonExe(), [path.join(ROOT, 'tools', 'zoe_server.py')],
      { cwd: ROOT, stdio: 'ignore' });
  } catch (e) { console.error('telemetry start failed', e); }
}

// ---- the Zoe window ----
function createWindow() {
  win = new BrowserWindow({
    width: 1440, height: 900, minWidth: 980, minHeight: 640,
    backgroundColor: '#01030a', show: false, autoHideMenuBar: true, icon: icon(),
    title: 'Zoe',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,      // renderer cannot touch Node directly
      nodeIntegration: false,      // no require() in the renderer
      sandbox: true,
    },
  });

  const tryLive = () => win.loadURL(`http://127.0.0.1:${TELEMETRY_PORT}`);
  tryLive();
  // if the telemetry server is not up yet, retry, then fall back to the local file
  win.webContents.on('did-fail-load', () => {
    setTimeout(() => {
      win.loadURL(`http://127.0.0.1:${TELEMETRY_PORT}`).catch(() =>
        win.loadFile(path.join(ROOT, 'zoe-ui', 'index.html')));
    }, 900);
  });

  win.once('ready-to-show', () => win.show());
  // minimize to tray instead of quitting
  win.on('close', (e) => {
    if (!app.isQuitting) { e.preventDefault(); win.hide(); }
  });
}

// ---- tray + menu ----
function buildTray() {
  tray = new Tray(icon());
  tray.setToolTip('Zoe');
  refreshTrayMenu();
  tray.on('double-click', showWindow);
}
function refreshTrayMenu() {
  const wsItems = wsm.list().map(w => ({ label: w.name, click: () => wsm.run(w) }));
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Show Zoe', click: showWindow },
    { label: 'Hide to tray', click: () => win && win.hide() },
    { type: 'separator' },
    { label: 'Workspaces', submenu: wsItems.length ? wsItems : [{ label: '(none yet)', enabled: false }] },
    { label: 'Voice', submenu: [
      { label: 'Start listening', click: startVoice },
      { label: 'Stop listening', click: stopVoice },
    ]},
    { type: 'separator' },
    { label: 'Launch on startup', type: 'checkbox',
      checked: app.getLoginItemSettings().openAtLogin,
      click: (mi) => app.setLoginItemSettings({ openAtLogin: mi.checked }) },
    { type: 'separator' },
    { label: 'Quit Zoe', click: () => { app.isQuitting = true; app.quit(); } },
  ]));
}
function showWindow() { if (win) { win.show(); win.focus(); } }

// ---- voice engine: the existing python assistant, managed by Electron ----
function startVoice() {
  if (voiceProc) return;
  voiceProc = spawn(pythonExe(), [path.join(ROOT, 'tools', 'zoe_assistant.py')],
    { cwd: ROOT, stdio: 'ignore', env: { ...process.env, ZOE_CONTROL: `http://127.0.0.1:${CONTROL_PORT}` } });
  voiceProc.on('exit', () => { voiceProc = null; sendVoiceState('off'); });
  sendVoiceState('listening');
}
function stopVoice() { if (voiceProc) { voiceProc.kill(); voiceProc = null; } sendVoiceState('off'); }
function sendVoiceState(s) { if (win && !win.isDestroyed()) win.webContents.send('voice:state', s); }

// ---- control endpoint: the voice assistant POSTs desktop commands here ----
function startControlServer() {
  controlServer = http.createServer((req, res) => {
    if (req.method !== 'POST') { res.writeHead(405); return res.end(); }
    let body = '';
    req.on('data', c => body += c);
    req.on('end', async () => {
      let data = {}; try { data = JSON.parse(body || '{}'); } catch {}
      let result = { handled: false };
      try {
        if (req.url === '/voice' && data.phrase) {
          const r = await wsm.runByPhrase(data.phrase);
          result = r.ok ? { handled: true, ...r } : { handled: false };
        } else if (req.url === '/action') {
          if (data.workspace) result = { handled: true, ...(await wsm.runByPhrase(data.workspace)) };
          else if (data.folder) result = { handled: true, ...launcher.openFolder(data.folder) };
          else if (data.launch) result = { handled: true, label: launcher.launchOne(data.launch, wsm.appMap()) };
          else if (data.url) result = { handled: true, ...launcher.openUrl(data.url) };
        }
      } catch (e) { result = { handled: false, error: String(e) }; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    });
  }).listen(CONTROL_PORT, '127.0.0.1');
}

// ---- IPC: the renderer (HUD) calls these via window.zoe ----
function registerIpc() {
  ipcMain.handle('workspaces:list', () => wsm.list());
  ipcMain.handle('workspace:run', (_e, name) => wsm.runByPhrase(name));
  ipcMain.handle('voice:phrase', (_e, phrase) => wsm.runByPhrase(phrase));
  ipcMain.handle('launch:target', (_e, target) => launcher.launchOne(target, wsm.appMap()));
  ipcMain.handle('open:folder', (_e, p) => launcher.openFolder(p));
  ipcMain.handle('open:url', (_e, u) => launcher.openUrl(u));
  ipcMain.handle('notify', (_e, { title, body }) => { new Notification({ title: title || 'Zoe', body: body || '' }).show(); return { ok: true }; });
  ipcMain.handle('startup:set', (_e, on) => { app.setLoginItemSettings({ openAtLogin: on }); return { ok: true }; });
  ipcMain.handle('startup:get', () => app.getLoginItemSettings().openAtLogin);
  ipcMain.handle('window:hide', () => { if (win) win.hide(); return { ok: true }; });
  ipcMain.handle('voice:start', () => { startVoice(); return { ok: true }; });
  ipcMain.handle('voice:stop', () => { stopVoice(); return { ok: true }; });
}

// ---- global shortcuts: push-to-talk + show/hide ----
function registerShortcuts() {
  globalShortcut.register('CommandOrControl+Shift+Space', () => {
    showWindow();
    if (win) win.webContents.send('push-to-talk');
    if (!voiceProc) startVoice();
  });
  globalShortcut.register('CommandOrControl+Shift+Z', () => {
    if (win && win.isVisible()) win.hide(); else showWindow();
  });
}

// ---- lifecycle ----
if (!app.requestSingleInstanceLock()) { app.quit(); }
else {
  app.on('second-instance', showWindow);
  app.whenReady().then(() => {
    startTelemetry();
    setTimeout(createWindow, 1100);   // give the telemetry server a moment
    buildTray();
    registerIpc();
    registerShortcuts();
    startControlServer();
    setTimeout(startVoice, 2600);   // always-listening for "Hey Zoe" once the app is up
    app.setLoginItemSettings({ openAtLogin: app.getLoginItemSettings().openAtLogin }); // keep current
  });
  app.on('window-all-closed', (e) => { /* stay alive in tray */ });
  app.on('will-quit', () => {
    globalShortcut.unregisterAll();
    if (telemetryProc) telemetryProc.kill();
    if (voiceProc) voiceProc.kill();
    if (controlServer) controlServer.close();
  });
}
