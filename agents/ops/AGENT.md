# Ops agent (scaffold)

Status: defined, NOT running. Turn on by enabling its workflow when you want it active.

Owns: keeping Zoey and her machine healthy -- the voice/app running, logs clean, deps installed,
tests green. When live, it routes to her existing `read_file` / `run_command` tools (the
investigate-and-fix path, confirm-before-destructive) and the VoltAgent infra/qa bundles
(`voltagent-infra:devops-incident-responder`, `voltagent-qa-sec:debugger`).

Escalates: anything destructive or outward-facing stops for confirmation; it never force-pushes or
rewrites git history (verification.md, git history is sacred).

Reads/writes: the Ops section of `agents/blackboard.md`.
