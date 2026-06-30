# Latest security report

This file is overwritten by `.github/workflows/zoe-security.yml` on each run with a one-screen
digest of the most recent scan (secrets / deps / SAST, pass or fail). The full machine-readable
report is uploaded as the workflow's `security-report` artifact.

_No GitHub Actions run yet. First scan ran in the cloud session: one open dependency CVE (PyNaCl),
no leaked secrets in the working tree. See `findings.md`._
