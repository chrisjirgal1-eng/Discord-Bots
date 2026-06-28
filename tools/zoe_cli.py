#!/usr/bin/env python3
"""Command-bar bridge: take a typed command and run it through the SAME pipeline as voice
(zoe_router.process), printing the explainable result as one line of JSON. The Electron command
bar spawns this; the voice loop calls zoe_router.process directly. One engine, two front ends.

  python tools/zoe_cli.py "open youtube and play lofi"
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jarvis_speak import load_env
import zoe_router

def main():
    load_env()
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print(json.dumps({"handled": False, "error": "empty command"}))
        return
    ctrl = os.environ.get("ZOE_CONTROL")          # set by Electron so native actions reach the app
    try:
        result = zoe_router.process(text, source="ui", ctrl=ctrl)
    except Exception as e:
        result = {"handled": False, "error": str(e), "text": text,
                  "parsed": "Error", "steps": [], "status": "failed"}
    print(json.dumps(result))                      # single JSON line on stdout

if __name__ == "__main__":
    main()
