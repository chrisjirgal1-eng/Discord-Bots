'use strict';
// Preload for the command bar (the palette window). Same security posture as the main HUD:
// contextIsolation ON, nodeIntegration OFF, one allow-listed bridge and nothing else.
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('zoeBar', {
  run: (text) => ipcRenderer.invoke('command:run', text),   // typed command -> shared pipeline
  image: (text, dataUrl) => ipcRenderer.invoke('command:image', { text, dataUrl }), // image + question -> vision
  history: () => ipcRenderer.invoke('command:history'),     // past commands from persisted state
  hide: () => ipcRenderer.invoke('palette:hide'),
  onShow: (cb) => ipcRenderer.on('palette:show', () => cb()),
});
