'use strict';
// Launcher: open apps, executables, scripts, folders, and URLs natively.
// Each target is either a string (classified heuristically) or an object with an
// explicit key: { app | path | exe | bat | ps1 | cmd | folder | url }.

const { shell } = require('electron');
const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

function isUrl(s) { return /^(https?:|mailto:)/i.test(s); }
function looksLikePath(s) { return /[\\/]/.test(s) || /\.[a-z0-9]{1,5}$/i.test(s); }

function runDetached(cmd, args, opts = {}) {
  const child = spawn(cmd, args, { detached: true, stdio: 'ignore', windowsHide: false, ...opts });
  child.unref();
}

// Launch a bare application or command by name. On Windows, `start` resolves PATH
// apps and many registered apps; an optional config/apps.json maps friendly names.
function launchApp(name, appMap) {
  const mapped = appMap && appMap[name.toLowerCase()];
  const target = mapped || name;
  if (looksLikePath(target) && fs.existsSync(target)) return launchPath(target);
  if (process.platform === 'win32') {
    exec(`start "" "${target}"`, { windowsHide: true }, () => {});
  } else if (process.platform === 'darwin') {
    exec(`open -a "${target}"`, () => {});
  } else {
    exec(`${target} &`, () => {});
  }
}

function launchPath(p) {
  const ext = path.extname(p).toLowerCase();
  if (ext === '.ps1') {
    runDetached('powershell.exe', ['-ExecutionPolicy', 'Bypass', '-File', p]);
  } else if (ext === '.bat' || ext === '.cmd') {
    runDetached('cmd.exe', ['/c', p]);
  } else if (ext === '.exe') {
    runDetached(p, []);
  } else {
    // a folder or document: let the OS open it with the default handler
    shell.openPath(p);
  }
}

// Open a folder (or reveal a file) in the OS file manager.
function openFolder(p) {
  if (!p) return { ok: false, error: 'no path' };
  const expanded = p.replace(/%([^%]+)%/g, (_, n) => process.env[n] || '');
  if (!fs.existsSync(expanded)) return { ok: false, error: 'not found: ' + expanded };
  shell.openPath(expanded);
  return { ok: true };
}

function openUrl(u) { shell.openExternal(u); return { ok: true }; }

// Run a raw command (cmd / powershell / terminal). Kept explicit so the AI cannot
// invoke it by accident: only items with an explicit { cmd } or { ps1 } key reach here.
function runCommand(command, kind) {
  if (kind === 'ps1' || kind === 'powershell') {
    runDetached('powershell.exe', ['-ExecutionPolicy', 'Bypass', '-Command', command]);
  } else {
    runDetached('cmd.exe', ['/c', command]);
  }
  return { ok: true };
}

// Launch a single target (string or object) and return a short label.
function launchOne(item, appMap) {
  try {
    if (typeof item === 'string') {
      if (isUrl(item)) return (openUrl(item), 'url ' + item);
      if (looksLikePath(item)) return (launchPath(item), 'path ' + item);
      return (launchApp(item, appMap), 'app ' + item);
    }
    if (item && typeof item === 'object') {
      if (item.url) return (openUrl(item.url), 'url ' + item.url);
      if (item.folder) return (openFolder(item.folder), 'folder ' + item.folder);
      if (item.path || item.exe) return (launchPath(item.path || item.exe), 'path ' + (item.path || item.exe));
      if (item.ps1) return (runCommand(item.ps1, 'ps1'), 'ps1');
      if (item.cmd) return (runCommand(item.cmd, 'cmd'), 'cmd');
      if (item.app) return (launchApp(item.app, appMap), 'app ' + item.app);
    }
  } catch (e) {
    return 'error ' + (e && e.message);
  }
  return 'skip';
}

module.exports = { launchOne, launchApp, launchPath, openFolder, openUrl, runCommand };
