#!/usr/bin/env python3
"""ZOE telemetry server: serves the live HUD and real system stats.

Reads Chris's actual CPU, RAM, disk, and network with psutil and exposes them at
/stats, and serves the HUD at /. Run it, then open http://localhost:7717.

  python tools/zoe_server.py
"""
import http.server, json, os, socket, time, psutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUD = os.path.join(ROOT, "zoe-ui", "index.html")
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

    def do_GET(self):
        if self.path.startswith("/stats"):
            self._send(200, json.dumps(stats()).encode(), "application/json")
        else:
            try:
                with open(HUD, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(404, b"zoe-ui/index.html not found", "text/plain")

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"ZOE online. Open http://localhost:{PORT}  (Ctrl+C to stop)")
    try:
        http.server.HTTPServer(("127.0.0.1", PORT), H).serve_forever()
    except KeyboardInterrupt:
        print("\nZOE offline.")
