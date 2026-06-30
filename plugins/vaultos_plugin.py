#!/usr/bin/env python3
"""ZOE plugin: VaultOS — research a video/reel into a viral breakdown.

A plugin_action with target "vaultos" (or any plugin_action carrying a video URL) is
routed here. It hands the URL to the VaultOS engine (default C:\\Users\\chris\\Zoe\\vault-os),
which downloads + transcribes + analyzes the video and writes an Obsidian breakdown into its
vault, then returns the note path, hook, score, and a spoken line.

Contract: plugin API 1.0.0 (see plugins/README.md). Fails safely: any problem returns
{"handled": False, "result": {...}} so the router can never be crashed by this plugin.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

PLUGIN = {
    "plugin_name": "vaultos",
    "plugin_version": "1.0.0",
    "schema_version": "1.0.0",
    "supported_intents": ["plugin_action"],
}

VAULTOS_DIR = os.environ.get("VAULTOS_DIR", r"C:\Users\chris\Zoe\vault-os")
_URL_RE = re.compile(r"https?://[^\s'\"]+")


def _find_url(command):
    payload = command.get("payload") or {}
    extra = payload.get("_extra") or {}
    for v in (payload.get("url"), command.get("target"), extra.get("url"),
              payload.get("text"), extra.get("text")):
        if isinstance(v, str):
            m = _URL_RE.search(v)
            if m:
                return m.group(0)
    return None


def _source(url):
    u = url.lower()
    if "instagram.com" in u:
        return "instagram"
    if "tiktok.com" in u:
        return "tiktok"
    return "youtube"


def _summary(note_path):
    try:
        text = Path(note_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None, None
    hook = score = None
    for ln in text.splitlines():
        if ln.startswith("> ") and hook is None:
            hook = ln[2:].strip()
        if "**Score:**" in ln and score is None:
            m = re.search(r"([\d.]+)/10", ln)
            if m:
                score = m.group(1)
    return hook, score


def execute(command):
    command = command or {}
    url = _find_url(command)
    if not url:
        return {"handled": False, "result": {
            "error": "no_url",
            "say": "Give me a video or reel link to research, sir."}}

    main_py = os.path.join(VAULTOS_DIR, "main.py")
    if not os.path.isfile(main_py):
        return {"handled": False, "result": {
            "error": "vaultos_missing", "path": main_py,
            "say": "I can't find the VaultOS engine, sir."}}

    source = _source(url)
    try:
        proc = subprocess.run(
            [sys.executable, main_py, "--url", url, "--source", source],
            cwd=VAULTOS_DIR, capture_output=True, text=True,
            encoding="utf-8", errors="ignore", timeout=600)
    except Exception as e:
        return {"handled": False, "result": {
            "error": "run_failed", "detail": str(e),
            "say": "VaultOS failed to run, sir."}}

    m = re.search(r"-> (.+\.md)\s*$", proc.stdout or "", re.MULTILINE)
    if not m:
        return {"handled": False, "result": {
            "error": "no_output", "log": ((proc.stdout or "") + (proc.stderr or ""))[-400:],
            "say": "I couldn't research that link, sir."}}

    note = m.group(1).strip()
    hook, score = _summary(note)
    say = "Done, sir. Saved a breakdown to the vault"
    if hook:
        say += f'. The hook was: "{hook}"'
    if score:
        say += f". Score {score} out of ten."
    return {"handled": True, "result": {
        "note": note, "hook": hook, "score": score,
        "source": source, "url": url, "say": say}}
