'use strict';
// Workspace Manager: discover and run workspaces from the workspaces/ directory.
// Each workspace is workspaces/<Name>/workspace.json. Users edit these files to add
// apps, websites, folders, scripts, aliases, order, and delays. No code changes needed.

const fs = require('fs');
const path = require('path');
const launcher = require('./launcher');

function norm(s) { return String(s || '').toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim(); }

class WorkspaceManager {
  constructor(rootDir, configDir) {
    this.dir = rootDir;                       // .../workspaces
    this.configDir = configDir;               // .../electron/config (for apps.json)
  }

  appMap() {
    try {
      const p = path.join(this.configDir, 'apps.json');
      return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, 'utf8')) : {};
    } catch { return {}; }
  }

  list() {
    const out = [];
    if (!fs.existsSync(this.dir)) return out;
    for (const entry of fs.readdirSync(this.dir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const file = path.join(this.dir, entry.name, 'workspace.json');
      if (!fs.existsSync(file)) continue;
      try {
        const ws = JSON.parse(fs.readFileSync(file, 'utf8'));
        ws.name = ws.name || entry.name;
        ws._dir = path.join(this.dir, entry.name);
        out.push(ws);
      } catch (e) {
        out.push({ name: entry.name, error: 'bad json: ' + e.message });
      }
    }
    return out;
  }

  // Match a spoken phrase to a workspace by name or alias. Returns the workspace or null.
  match(phrase) {
    const p = norm(phrase);
    if (!p) return null;
    let best = null;
    for (const ws of this.list()) {
      const keys = [ws.name, ...(ws.aliases || [])].map(norm).filter(Boolean);
      for (const k of keys) {
        if (p === k || p.includes(k) || k.includes(p)) {
          // prefer the longest match so "coding" does not beat "start coding"
          if (!best || k.length > best.len) best = { ws, len: k.length };
        }
      }
    }
    return best ? best.ws : null;
  }

  async run(ws) {
    if (!ws) return { ok: false, error: 'no workspace' };
    const appMap = this.appMap();
    const delay = Number(ws.delayMs || ws.launchDelay || 600);
    const log = [];
    const items = Array.isArray(ws.launch) ? ws.launch : [];
    for (const item of items) {
      log.push(launcher.launchOne(item, appMap));
      await new Promise(r => setTimeout(r, delay));
    }
    for (const f of (ws.folders || [])) {
      const r = launcher.openFolder(f);
      log.push(r.ok ? 'folder ' + f : 'folder-miss ' + f);
    }
    for (const f of (ws.files || [])) log.push(launcher.launchOne({ path: f }, appMap));
    for (const url of (ws.websites || [])) {
      log.push(launcher.launchOne(url, appMap));
      await new Promise(r => setTimeout(r, 250));
    }
    if (ws.startupScript) log.push(launcher.launchOne({ ps1: ws.startupScript }, appMap));
    return { ok: true, name: ws.name, launched: log };
  }

  async runByPhrase(phrase) {
    const ws = this.match(phrase);
    if (!ws) return { ok: false, error: 'no workspace matched: ' + phrase };
    return this.run(ws);
  }
}

module.exports = WorkspaceManager;
