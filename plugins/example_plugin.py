#!/usr/bin/env python3
"""Example ZOE plugin: the reference implementation of the versioned plugin contract.

A plugin is a Python module that exposes a module-level PLUGIN metadata dict and an
execute(command) function. The router loads it at startup and routes plugin_action commands
whose target matches this plugin's name (or whose intent is in supported_intents).

Contract (all required):
  PLUGIN = {plugin_name, plugin_version, schema_version, supported_intents}
  execute(command) -> {"handled": bool, "result": {...}}

Rules: a plugin MUST NOT bypass the router, MUST NOT modify core files, MUST fail safely
(raise nothing the router cannot catch), MUST return a structured response, and MUST stay
backward compatible. The router isolates a misbehaving plugin so it can never crash the system.
"""

PLUGIN = {
    "plugin_name": "example",
    "plugin_version": "1.0.0",
    "schema_version": "1.0.0",
    "supported_intents": ["plugin_action"],
}

def execute(command):
    """Echo the command payload back as a structured result. Pure, no side effects, always safe."""
    command = command or {}
    payload = command.get("payload") or {}
    return {
        "handled": True,
        "result": {
            "plugin": PLUGIN["plugin_name"],
            "message": "example plugin received your command",
            "target": command.get("target", ""),
            "echo": payload,
        },
    }
