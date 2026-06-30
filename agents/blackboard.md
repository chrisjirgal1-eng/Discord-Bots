# Blackboard

The shared state for Zoey's agents. Each agent reads only its own section and writes its last
action + open items here. The evolving loop reads the whole board to decide the next move. Keep
entries short; this file is read on every loop run, so cheap-to-read matters.

## Current focus

Phase 1 shipped: the security agent (free scanners) + the video list + creator registry. Next:
the evolving loop workflow, then the agent scaffolds, then the live UI.

## Security agent

- Last run: pending first GitHub Actions run.
- Open: PyNaCl 1.5.0 has CVE-2025-69277 (fix 1.6.2). requirements.txt allows <2.0.0, so a bump to
  >=1.6.2 closes it. Flagged for the evolving loop to fix in a PR.
- Posture: confirm-before-irreversible; the agent only reports + proposes, it does not push fixes
  itself (the evolving loop opens a PR a human merges).

## Content agent

Scaffold only. Not running.

## Research agent

Scaffold only. Not running.

## Ops agent

Scaffold only. Not running.

## Evolving loop

Not enabled yet (needs the ANTHROPIC_API_KEY repo secret). Once on: one verified improvement per
run, opens a PR, appends a lesson, updates this board.
