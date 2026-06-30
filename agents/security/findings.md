# Security findings log

Running log the security agent appends to. Newest at the bottom. Each finding: date, severity,
what, where, fix. The evolving loop reads the open ones and proposes PRs.

## 2026-06-30 (first scan, in the cloud session)

- [open] MEDIUM. Dependency CVE: PyNaCl 1.5.0 -> CVE-2025-69277, fixed in 1.6.2. Source:
  pip-audit on requirements.txt. Fix: bump the PyNaCl pin to >=1.6.2 (current pin allows <2.0.0).
- [accepted] HIGH (by design). bandit flags `subprocess` with `shell=True` in `tools/zoe_ops.py`.
  This is intentional (she runs shell commands to fix things) and guarded by a danger-list +
  confirm-before-destructive. Not a vulnerability to fix; documented here so it is not re-flagged.
- [info] bandit: 78 low / 11 medium across tools/. Mostly subprocess + try/except/pass patterns
  in best-effort code. Reviewed; none are exploitable. The agent will surface only NEW issues
  beyond this baseline going forward.
