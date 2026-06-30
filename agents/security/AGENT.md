# Security agent

Zoey's self-hardening agent: keeps her code and the machine she runs on safe from the obvious
ways people get owned. It is the first live agent because it is free (deterministic scanners, no
LLM tokens), runs on GitHub Actions, and directly answers "harden her against hackers."

## What it scans (all free, all on Ubuntu via GitHub Actions)

- **Secrets** (`gitleaks`): scans the whole git history + working tree for leaked keys/tokens.
  This is the one that matters most here -- API keys have been pasted by accident before, and a
  leaked key in history is a real breach. Fails the run if a secret is found.
- **Python deps** (`pip-audit`): CVEs in `requirements.txt` / `tools/requirements.txt`. Already
  caught PyNaCl 1.5.0 -> CVE-2025-69277 (fix 1.6.2).
- **Node deps** (`npm audit`): CVEs in the Electron app's `package.json`.
- **Python SAST** (`bandit`): risky code patterns. Known/accepted ones (the intentional
  `shell=True` in `tools/zoe_ops.py`, guarded by a danger-list) are expected; the agent surfaces
  only new high/medium issues.
- **Multi-language SAST** (`semgrep`, security-audit ruleset): broader pattern scan.

## Schedule

Runs on every push to the default branch + daily cron (`.github/workflows/zoe-security.yml`).
Uploads the full report as a workflow artifact and writes a one-screen digest to
`agents/security/latest-report.md`.

## How it escalates

The scanners only REPORT. When a finding needs a code change (e.g. bump PyNaCl), the agent logs
it to `agents/security/findings.md` + the blackboard, and the evolving loop picks it up and opens
a PR with the fix. A human merges. The agent never pushes a change itself, and never weakens the
deny-list / catastrophic-command guards. This is the confirm-before-irreversible posture.

## What it does NOT do

No offensive tooling, no scanning of anything outside this repo + the local machine baseline, no
auto-merging. It hardens; it does not attack.
