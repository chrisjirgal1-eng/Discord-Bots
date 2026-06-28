#!/usr/bin/env python3
"""ZOE version contracts: the single place the system's versions live.

Forward-compatibility law (the kernel rule): upgrades are additive only, old fields are never
removed, unknown fields are ignored or preserved, and a version MISMATCH degrades to fallback
mode, never a crash. compatible() decides by MAJOR version: same major = compatible; a different
major still runs, just flagged as fallback.
"""

SYSTEM = {
    "system_name": "ZOE",
    "core_version": "1.0.0",
    "command_schema_version": "1.0.0",
    "plugin_api_version": "1.0.0",
    "state_schema_version": "1.0.0",
}

def _major(v):
    try:
        return int(str(v).split(".")[0])
    except Exception:
        return -1

def compatible(their_version, our_version):
    """Same major version = compatible. Anything else = run in fallback mode, never fail."""
    return _major(their_version) >= 0 and _major(their_version) == _major(our_version)

if __name__ == "__main__":
    import json
    print(json.dumps(SYSTEM, indent=2))
