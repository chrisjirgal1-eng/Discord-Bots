#!/usr/bin/env python3
"""Zoe's Roblox capability: find/launch Roblox Studio and report the Roblox environment, so she can
operate Studio (via see_screen + screen_task) and code for it. Studio saves to the Roblox cloud by
default; for robust file-based Luau coding, a Rojo project is the pro path. Best-effort, never raises.
"""
import os, subprocess, shutil
from pathlib import Path

HOME = Path(os.path.expanduser("~"))


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
    return bool(shutil.which("rojo"))


def find_projects():
    out = []
    for root in (HOME / "Documents", HOME / "Desktop", Path(r"C:\Users\chris\Zoe")):
        if root.exists():
            try:
                out += [str(p.parent) for p in list(root.glob("**/default.project.json"))[:10]]
            except Exception:
                pass
    return out[:10]


def launch():
    exe = studio_exe()
    if not exe:
        return {"ok": False, "error": "Roblox Studio not found on this machine"}
    try:
        subprocess.Popen([exe])
        return {"ok": True, "launched": exe}
    except Exception as e:
        return {"ok": False, "error": str(e)[:150]}


def status():
    return {"installed": bool(studio_exe()), "exe": studio_exe(), "running": is_running(),
            "rojo": rojo_installed(), "projects": find_projects()}


if __name__ == "__main__":
    import pprint
    pprint.pprint(status())
