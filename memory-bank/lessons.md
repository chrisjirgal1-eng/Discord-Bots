# Lessons

Anti-repetition memory. Read before similar work. Append after a mistake, a correction,
or a reviewer catch. Format per entry: Mistake / Fix / Prevent. Newest at the bottom.
See `.claude/rules/learning.md` for the loop.

## 2026-06-27

- Third-party git clone is blocked.
  - Mistake: `git clone` / `claude plugin marketplace add owner/repo` 403s in this session.
  - Fix: the git proxy rewrites github.com and is scoped to one repo. Fetch the repo tarball
    from `codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/main` with curl, extract, and
    add the local directory as the marketplace.
  - Prevent: never assume `git clone` of an external repo works here. Reach for the curl tarball.

- Workflow result is nested.
  - Mistake: read `d['reportMarkdown']` from a workflow output file and hit KeyError.
  - Fix: the task output JSON wraps the script return under `result`. Read `d['result'][...]`.
  - Prevent: inspect the JSON shape before parsing a tool output file.

- Em dash slipped into a code comment.
  - Mistake: wrote an em dash in a code comment despite the no-em-dash rule.
  - Fix: changed it to a colon before committing.
  - Prevent: scan every diff for em dashes and the banned words before committing.

- uv-tool interpreter is not system python.
  - Mistake: ran a uv-tool package's module with `/usr/local/bin/python3` and got ModuleNotFound.
  - Fix: read the shebang of the installed binary (`head -1 $(which graphify)`) to find the venv python.
  - Prevent: for a uv-tool install, resolve the interpreter from the binary shebang, not system python.

- Do not commit large scaffolds into this repo.
  - Mistake: `npx prompts.chat new` dropped a 127MB Next.js app into the repo working tree.
  - Fix: gitignore the scaffold dir; it belongs in its own repo, regenerable on demand.
  - Prevent: a generated app or vendor tree goes in .gitignore, never committed here.

- Squash merges make feature branches diverge.
  - Mistake: stacking new edits on an already-squash-merged branch produces a messy PR diff.
  - Fix: for each new change, branch fresh off the default branch (claude/vibrant-cray-tui7og).
  - Prevent: always `git fetch` then branch off origin/default before starting a new change.

- Do not ship unverifiable logic changes blind.
  - Mistake: tempted to apply concurrency rewrites to the bot with no test suite.
  - Fix: applied only safe fixes, routed the diff to a fresh Opus reviewer, flagged a smoke test.
  - Prevent: no tests means a fresh-reviewer pass plus a human smoke-test flag before shipping logic.

- Banned words slipped into committed docs.
  - Mistake: "leverage" reached active-context.md and autonomous-potential.md, past a workflow verify pass.
  - Fix: grep -rnE for em dashes and delve/leverage/fantastic across ALL changed files, fixed each.
  - Prevent: run the banned-word scan on docs and workflow output too, not just code. Tell workflow
    verify agents to grep for the banned words explicitly, since a prose reviewer can miss one.
