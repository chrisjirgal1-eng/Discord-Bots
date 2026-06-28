#!/usr/bin/env python3
"""ZOE telemetry server: serves the live HUD and real system stats.

Reads Chris's actual CPU, RAM, disk, and network with psutil and exposes them at
/stats, and serves the HUD at /. Run it, then open http://localhost:7717.

  python tools/zoe_server.py
"""
import http.server, json, os, socket, sys, time, urllib.parse, psutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_memory          # Obsidian memory API; optional
except Exception:
    zoe_memory = None
try:
    from jarvis_speak import load_env
    load_env()                 # so POST /command's classify has the Groq key from .env
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD = os.path.join(ROOT, "zoe-ui", "index.html")
HUD3D = os.path.join(ROOT, "zoe-ui", "os3d.html")
HUDVAULT = os.path.join(ROOT, "zoe-ui", "vault.html")
HUDSHELL = os.path.join(ROOT, "zoe-ui", "shell.html")
PORT = 7717

_n = psutil.net_io_counters()
_prev = {"t": time.time(), "sent": _n.bytes_sent, "recv": _n.bytes_recv}
psutil.cpu_percent(percpu=True)  # prime the first reading

def stats():
    global _prev
    now = time.time()
    n = psutil.net_io_counters()
    dt = max(now - _prev["t"], 0.001)
    up = (n.bytes_sent - _prev["sent"]) / dt / 1024
    down = (n.bytes_recv - _prev["recv"]) / dt / 1024
    _prev = {"t": now, "sent": n.bytes_sent, "recv": n.bytes_recv}
    vm = psutil.virtual_memory()
    cores = psutil.cpu_percent(percpu=True)
    try:
        disk = psutil.disk_usage("C:/").percent
    except Exception:
        disk = psutil.disk_usage("/").percent
    return {
        "host": socket.gethostname(),
        "cpu": round(sum(cores) / len(cores), 1),
        "cores": [round(c, 1) for c in cores],
        "ram": vm.percent,
        "ram_used_gb": round(vm.used / 1e9, 1),
        "ram_total_gb": round(vm.total / 1e9, 1),
        "disk": round(disk, 1),
        "net_up": round(max(up, 0), 1),
        "net_down": round(max(down, 0), 1),
        "procs": len(psutil.pids()),
        "uptime": int(now - psutil.boot_time()),
        "time": time.strftime("%H:%M:%S"),
        "date": time.strftime("%a %d %b %Y").upper(),
    }

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_GET(self):
        if self.path.startswith("/stats"):
            self._json(stats())
        elif self.path.startswith("/memory/read"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("q", [None])[0]
            self._json(zoe_memory.read(q) if zoe_memory else {"error": "memory unavailable"})
        elif self.path.startswith("/session/resume"):
            self._json(zoe_memory.resume() if zoe_memory else {"error": "memory unavailable"})
        elif self.path.startswith("/memory/graph"):
            self._json(zoe_memory.graph() if zoe_memory else {"nodes": [], "edges": []})
        elif self.path.startswith("/memory/list"):
            self._json(zoe_memory.list_notes() if zoe_memory else {})
        elif self.path.startswith("/3d") or self.path.startswith("/os3d"):
            self._html(HUD3D, b"zoe-ui/os3d.html not found")
        elif self.path.startswith("/vault"):
            self._html(HUDVAULT, b"zoe-ui/vault.html not found")
        elif self.path.startswith("/shell"):
            self._html(HUDSHELL, b"zoe-ui/shell.html not found")
        else:
            self._html(HUD, b"zoe-ui/index.html not found")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if self.path.startswith("/memory/write") and zoe_memory:
            p = zoe_memory.write(data.get("title", "note"), data.get("content", ""),
                                 data.get("folder", "notes"), data.get("tags"))
            self._json({"ok": True, "path": p})
        elif self.path.startswith("/memory/sync") and zoe_memory:
            self._json({"ok": True, "path": zoe_memory.sync()})
        elif self.path.startswith("/command"):
            try:
                import zoe_router          # the one shared pipeline (same as voice + command bar)
                self._json(zoe_router.process(data.get("text", ""), source="ui3d"))
            except Exception as e:
                self._json({"handled": False, "parsed": "Error", "steps": [],
                            "error": str(e), "status": "failed"}, 200)
        else:
            self._json({"ok": False, "error": "unknown route"}, 404)

    def _html(self, path, missing):
        try:
            with open(path, "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        except FileNotFoundError:
            self._send(404, missing, "text/plain")

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"ZOE online. Open http://localhost:{PORT}  (Ctrl+C to stop)")
    try:
        # threaded so a slow /command (Groq ~1s) never blocks /stats polling or the UI
        http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
    except OSError as e:
        print(f"ZOE telemetry could not bind port {PORT} (already in use?): {e}")
    except KeyboardInterrupt:
        print("\nZOE offline.")
