'use strict';
// Preload: the only bridge between the renderer (the Zoe HUD) and the main process.
// contextIsolation is ON and nodeIntegration is OFF, so the renderer gets exactly this
// allow-listed API and nothing else (no require, no fs, no child_process).

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('zoe', {
  // workspaces + launching
  listWorkspaces: () => ipcRenderer.invoke('workspaces:list'),
  runWorkspace: (name) => ipcRenderer.invoke('workspace:run', name),
  runPhrase: (phrase) => ipcRenderer.invoke('voice:phrase', phrase),
  launch: (target) => ipcRenderer.invoke('launch:target', target),
  openFolder: (p) => ipcRenderer.invoke('open:folder', p),
  openUrl: (u) => ipcRenderer.invoke('open:url', u),

  // desktop
  notify: (title, body) => ipcRenderer.invoke('notify', { title, body }),
  setLaunchOnStartup: (on) => ipcRenderer.invoke('startup:set', !!on),
  getLaunchOnStartup: () => ipcRenderer.invoke('startup:get'),
  minimizeToTray: () => ipcRenderer.invoke('window:hide'),

  // persistent state (read-only from the renderer)
  getState: () => ipcRenderer.invoke('state:get'),

  // voice engine (the python assistant) control + status
  startVoice: () => ipcRenderer.invoke('voice:start'),
  stopVoice: () => ipcRenderer.invoke('voice:stop'),
  onVoiceState: (cb) => ipcRenderer.on('voice:state', (_e, s) => cb(s)),
  onPushToTalk: (cb) => ipcRenderer.on('push-to-talk', () => cb()),

  platform: process.platform,
  isElectron: true,
});
