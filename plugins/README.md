# Zoe plugins

Drop a `*.py` file in this folder to add a capability. The router scans this folder at startup,
validates each plugin against the versioned contract, and registers the good ones into its
lookup table. A bad plugin is isolated and skipped; it never blocks the others or the system.

## Contract (plugin API 1.0.0)

Each plugin module must expose:

```python
PLUGIN = {
    "plugin_name": "example",          # unique name; plugin_action commands target it by name
    "plugin_version": "1.0.0",
    "schema_version": "1.0.0",         # plugin API version it was written against
    "supported_intents": ["plugin_action"],
}

def execute(command):                  # command is the locked command schema (see the guide)
    return {"handled": True, "result": {...}}
```

## Rules

- Must NOT bypass the router. Plugins are called by `zoe_router.route()`, never directly by the UI.
- Must NOT modify core files or global state.
- Must fail safely and return a structured `{"handled": bool, "result": {...}}`.
- Must stay backward compatible: additive changes only, never remove fields.
- A plugin whose `schema_version` is a different MAJOR than the plugin API version is skipped
  (fallback), not loaded, so an incompatible plugin can never break startup.

## How it is routed

A command with `intent: "plugin_action"` and `target: "<plugin_name>"` is dispatched to that
plugin's `execute(command)`. See `example_plugin.py` (echo) and `clock_plugin.py` (returns the
time) for working references, and `COMMAND_SYSTEM_GUIDE.md` for the command schema and the
full pipeline.
