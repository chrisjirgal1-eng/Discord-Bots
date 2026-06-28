# Zoe runtime state

`zoe_state.json` lives here: Zoe's session continuity (session context, last commands, workspace
state, preferences, system mode). It is written by `tools/zoe_state.py` (the single writer) and
read by the Electron app for restore. It is generated at runtime and gitignored, so it is not in
the repo; Zoe creates it from safe defaults on first run.

This is distinct from `memory-bank/`, which is the durable project memory and IS committed.
