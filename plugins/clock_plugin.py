#!/usr/bin/env python3
"""Clock ZOE plugin: a second reference plugin that does something real (returns the time).

Shows that multiple plugins coexist and are routed by name. Stdlib only, no side effects.
"""
import time

PLUGIN = {
    "plugin_name": "clock",
    "plugin_version": "1.0.0",
    "schema_version": "1.0.0",
    "supported_intents": ["plugin_action"],
}

def execute(command):
    """Return the current local date and time as a structured result."""
    return {
        "handled": True,
        "result": {
            "plugin": PLUGIN["plugin_name"],
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "epoch": int(time.time()),
        },
    }
