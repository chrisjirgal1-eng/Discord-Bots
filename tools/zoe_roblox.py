#!/usr/bin/env python3
"""Zoe's Roblox capability: find/launch Roblox Studio, run the Rojo file-sync server, and write Luau
as real files in the Rojo project so she can code reliably (not by typing into the editor). She still
uses see_screen + screen_task to operate the Studio GUI. Best-effort, never raises.

Setup done: Rojo 7.6.x at ~/.local/bin/rojo.exe, project at RobloxProjects/zenthra. One-time manual
step: install the "Rojo" plugin in Studio (marketplace), then it connects to `rojo serve`.
"""
import os, subprocess, shutil
from pathlib import Path

HOME = Path(os.path.expanduser("~"))
ROJO = HOME / ".local" / "bin" / "rojo.exe"
PROJECT = HOME / "RobloxProjects" / "zenthra"
SRC = {"server": PROJECT / "src" / "server", "client": PROJECT / "src" / "client",
       "shared": PROJECT / "src" / "shared"}
_EXT = {"server": ".server.luau", "client": ".client.luau", "shared": ".luau"}


def studio_exe():
    base = HOME / "AppData" / "Local" / "Roblox" / "Versions"
    if not base.exists():
        return ""
    hits = sorted(base.glob("*/RobloxStudioBeta.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(hits[0]) if hits else ""


def is_running():
    try:
        import psutil
        return any("RobloxStudioBeta" in (p.info.get("name") or "") for p in psutil.process_iter(["name"]))
    except Exception:
        return False


def rojo_installed():
    return ROJO.exists() or bool(shutil.which("rojo"))


def _serving():
    try:
        import psutil
        return any("rojo" in (p.info.get("name") or "").lower() and "serve" in " ".join(p.info.get("cmdline") or [])
                   for p in psutil.process_iter(["name", "cmdline"]))
    except Exception:
        return False


def launch():
    exe = studio_exe()
    if not exe:
        return {"ok": False, "error": "Roblox Studio not found on this machine"}
    try:
        subprocess.Popen([exe])
        return {"ok": True, "launched": exe}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def serve():
    """Start the Rojo sync server (detached) so the Studio plugin syncs the project live."""
    if not PROJECT.exists():
        return {"ok": False, "error": "Rojo project not found"}
    if _serving():
        return {"ok": True, "already": True, "detail": "rojo serve already running"}
    try:
        subprocess.Popen([str(ROJO), "serve"], cwd=str(PROJECT),
                         creationflags=0x00000008)  # DETACHED
        return {"ok": True, "detail": "rojo serve started; connect the Rojo plugin in Studio"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def write_script(name, code, side="server"):
    """Write a Luau script as a file in the Rojo project (side: server/client/shared). Rojo syncs it
    into Studio. Returns {ok, path}."""
    side = side if side in SRC else "server"
    safe = "".join(c for c in (name or "Script") if c.isalnum() or c in "_-") or "Script"
    try:
        SRC[side].mkdir(parents=True, exist_ok=True)
        p = SRC[side] / (safe + _EXT[side])
        p.write_text(code or "-- (empty)\n", encoding="utf-8")
        return {"ok": True, "path": str(p), "side": side}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def status():
    return {"installed": bool(studio_exe()), "exe": studio_exe(), "running": is_running(),
            "rojo": rojo_installed(), "project": str(PROJECT) if PROJECT.exists() else "",
            "serving": _serving()}


if __name__ == "__main__":
    import pprint
    pprint.pprint(status())
