#!/usr/bin/env python3
"""ZOE telemetry server: serves the live HUD and real system stats.

Reads Chris's actual CPU, RAM, disk, and network with psutil and exposes them at
/stats, and serves the HUD at /. Run it, then open http://localhost:7717.

  python tools/zoe_server.py
"""
import http.server, json, os, socket, sys, threading, time, urllib.parse, psutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import zoe_memory          # Obsidian memory API; optional
except Exception:
    zoe_memory = None
try:
    import zoe_research        # bridge to the C:\Users\chris\Zoe research second-brain; optional
except Exception:
    zoe_research = None
try:
    import zoe_ops_loop        # the local ops loop engine (/ops workspace); optional
except Exception:
    zoe_ops_loop = None
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
HUDLAB = os.path.join(ROOT, "zoe-ui", "research.html")
HUDOPS = os.path.join(ROOT, "zoe-ui", "ops.html")
HUDECO = os.path.join(ROOT, "zoe-ui", "ecosystem.html")
ECO_OS = r"C:\Users\chris\Zoe\os"   # the Zoe OS layer (registry + activity)


def _eco_registry():
    """Trimmed registry for the Ecosystem UI. Safe: empty on error."""
    try:
        with open(os.path.join(ECO_OS, "registry.json"), encoding="utf-8") as f:
            d = json.load(f)
        res = [{k: r.get(k) for k in ("name", "category", "description", "tags", "launch_command", "location")}
               for r in d.get("resources", [])]
        return {"count": d.get("count"), "generated": d.get("generated"),
                "by_category": d.get("by_category", {}), "flags": d.get("flags", {}), "resources": res}
    except Exception as e:
        return {"count": 0, "by_category": {}, "resources": [], "error": str(e)[:120]}


def _eco_activity(n=24):
    """Recent Zoe OS activity events, newest first. [] on error."""
    try:
        out = []
        with open(os.path.join(ECO_OS, "activity.jsonl"), encoding="utf-8") as f:
            for ln in f.read().splitlines()[-n:]:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
        return list(reversed(out))
    except Exception:
        return []
CONFIG_JSON = os.path.join(ROOT, "zoe-ui", "config.json")
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
        elif self.path.startswith("/config"):
            try:
                with open(CONFIG_JSON) as f:
                    self._json(json.load(f))
            except FileNotFoundError:
                # generate on-demand if config.json is missing
                try:
                    import zoe_status
                    self._json(zoe_status.build())
                except Exception as e:
                    self._json({"error": str(e)}, 500)
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
        elif self.path.startswith("/research/agents"):
            self._json(zoe_research.agents() if zoe_research else {"error": "research bridge unavailable"})
        elif self.path.startswith("/research/capabilities"):
            self._json(zoe_research.capabilities() if zoe_research else {"error": "research bridge unavailable"})
        elif self.path.startswith("/research/creators"):
            self._json(zoe_research.creators() if zoe_research else {"error": "research bridge unavailable"})
        elif self.path.startswith("/research/watchlist"):
            self._json(zoe_research.watchlist() if zoe_research else {"error": "research bridge unavailable"})
        elif self.path.startswith("/research/summary"):
            self._json(zoe_research.summary() if zoe_research else {"error": "research bridge unavailable"})
        elif self.path.startswith("/research/voice"):
            self._json(zoe_research.voice() if zoe_research else {"error": "research bridge unavailable"})
        elif self.path.startswith("/research/search"):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("q", [""])[0]
            self._json(zoe_research.search(q) if zoe_research else {"error": "research bridge unavailable"})
        elif self.path.startswith("/research") or self.path.startswith("/lab"):
            self._html(HUDLAB, b"zoe-ui/research.html not found")
        elif self.path.startswith("/ecosystem/data"):
            self._json(_eco_registry())
        elif self.path.startswith("/ecosystem/activity"):
            self._json(_eco_activity())
        elif self.path.startswith("/ecosystem") or self.path.startswith("/os"):
            self._html(HUDECO, b"zoe-ui/ecosystem.html not found")
        elif self.path.startswith("/ops/log"):
            self._json({"runs": zoe_ops_loop.read_log()} if zoe_ops_loop else {"runs": [], "error": "ops loop unavailable"})
        elif self.path.startswith("/ops/status"):
            self._json(zoe_ops_loop.status() if zoe_ops_loop else {"error": "ops loop unavailable"})
        elif self.path.startswith("/ops"):
            self._html(HUDOPS, b"zoe-ui/ops.html not found")
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
        elif self.path.startswith("/ops/run") and zoe_ops_loop:
            try:
                self._json(zoe_ops_loop.run_once(data.get("task") or None))
            except Exception as e:
                self._json({"status": "ERROR", "error": str(e)}, 200)
        elif self.path.startswith("/ops/config") and zoe_ops_loop:
            self._json(zoe_ops_loop.set_config(data))
        elif self.path.startswith("/ops/act") and zoe_ops_loop:
            try:
                self._json(zoe_ops_loop.act_once(data.get("task") or None))
            except Exception as e:
                self._json({"status": "ERROR", "error": str(e)}, 200)
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

def _free_port(port):
    """Best-effort: kill any process already listening on the port (a stale Zoe server) so we can
    bind. This is the fix for 'Backend offline' on relaunch: a leftover server held 7717 and the
    new one could not bind, so the UI fell back to simulated stats."""
    try:
        for c in psutil.net_connections(kind="inet"):
            if c.laddr and c.laddr.port == port and c.status == psutil.CONN_LISTEN and c.pid:
                try:
                    psutil.Process(c.pid).kill()
                except Exception:
                    pass
    except Exception:
        pass


if __name__ == "__main__":
    # threaded so a slow /command (Groq ~1s) never blocks /stats polling or the UI
    server = None
    for attempt in range(4):
        try:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H)
            break
        except OSError as e:
            print(f"port {PORT} busy ({e}); clearing a stale server and retrying...")
            _free_port(PORT)
            time.sleep(0.6)
    if not server:
        print(f"ZOE telemetry could not bind port {PORT} after retries.")
        sys.exit(1)
    print(f"ZOE online. Open http://localhost:{PORT}  (Ctrl+C to stop)")
    if zoe_ops_loop:
        threading.Thread(target=zoe_ops_loop.serve_scheduler, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nZOE offline.")
