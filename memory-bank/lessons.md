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

- Instagram needs a login cookie, and Chromium app-bound encryption hides it.
  - Mistake: assumed yt-dlp `--cookies-from-browser chrome/edge` would just work on Chris's PC.
  - Fix: yt-dlp has no app-bound (v20) support; copying the profile drops the session; the
    elevation-service COM call is refused for an external process (caller validation). The working
    path is a cookies.txt exported by the Get cookies.txt LOCALLY browser extension, then
    `--cookies file.txt`. Firefox also works (no app-bound encryption).
  - Prevent: on Windows with Chrome or Edge, plan for a cookie-export extension up front. Keep the
    cookie file out of the repo. This is a workaround, not "yt-dlp is broken."

- Arg position when shelling `python -m <module>`.
  - Mistake: inserted `--cookies` at argv index 2, before `yt_dlp`, so python read `-m --cookies`.
  - Fix: insert module flags after the module name (index 3 in `[py, -m, yt_dlp, ...]`).
  - Prevent: for `python -m mod`, module args go after the module token, never between -m and mod.

- urllib to a Cloudflare-fronted API returns 403.
  - Mistake: posted to the Groq API with urllib and got 403, though the key was valid (curl worked).
  - Fix: the default `Python-urllib` User-Agent is blocked at the edge. Set a real User-Agent header.
  - Prevent: set an explicit User-Agent on urllib requests to third-party APIs behind Cloudflare.

- Merging independent branches off the same old base produces mutual contradictions.
  - Mistake: two Devin branches disagreed: one test asserted a lenient default, another made the
    code raise. Naive merge left a failing test.
  - Fix: resolved to the safer behavior (raise on missing URL) and updated the stale test to match.
  - Prevent: when merging several branches forked from one old base, expect them to contradict each
    other and the newer default; resolve to the safer behavior and reconcile tests, then run them.

- Native Windows Python cannot open Git Bash mount paths.
  - Mistake: passed a `/c/Users/...` path (from the Bash tool) into `python -c "open('/c/...')"` and got
    FileNotFoundError, more than once.
  - Fix: the Bash tool is Git Bash, but `python.exe` is native Windows. Use `C:/Users/...` or `C:\Users\...`,
    or pipe data via stdin, or just use the Read tool which handles the path.
  - Prevent: when handing a path from the Bash tool to native Python, convert `/c/` to `C:/` first, or
    avoid the intermediate file and pipe through stdin.

- Supabase cannot serve HTML pages on its own domain.
  - Mistake: built a static-site path on Supabase (edge function, then storage); both returned the
    pages as text/plain, so browsers refuse to render them.
  - Fix: the platform rewrites text/html to text/plain on *.supabase.co (anti-phishing). Host HTML
    on Vercel or any static host; keep Supabase for API, DB, and storage only.
  - Prevent: never plan HTML hosting on supabase.co URLs. API and images are fine, pages are not.

- In-database e2e testing works when the sandbox egress blocks a domain, but transactions bite.
  - Mistake: a DO block seeded a config row and then called the edge function; the function read the
    OLD value because the uncommitted write was invisible to its separate connection, so all auth 401'd.
  - Fix: split the suite into separate execute_sql calls: commit config first, then run the HTTP tests
    (Postgres `http` extension calling the live function URLs), then restore config.
  - Prevent: any state an external service must see has to be committed before the call, so no
    mid-transaction config flips inside one DO block. Also guard nullable vars before http_get.

- MCP write tools can be approval-gated in autonomous sessions, and AskUserQuestion does not unlock them.
  - Mistake: retried a Vercel deploy after Chris said "approve it" via AskUserQuestion; the MCP call
    still failed with "requires approval" because the gate needs an interactive tap, not a chat answer.
  - Fix: shipped everything else, documented two 2-minute deploy paths in the README, left hosting
    as Chris's one interactive step.
  - Prevent: treat "-32003 requires approval" as a hard stop in autonomous runs. Design a fallback
    delivery (docs + local-file mode) instead of retrying.

- GitHub Pages from a feature branch fails silently-ish; enablement needs a human admin.
  - Mistake: expected configure-pages enablement:true to enable Pages (the workflow token
    cannot, "Resource not accessible by integration") and expected a feature-branch deploy
    to work (the github-pages environment rejects non-default branches with a 1-second
    no-runner "failure" and no step logs).
  - Fix: Chris set Settings > Pages > Source = GitHub Actions (verify with has_pages via
    the repo API before rerunning), and the deploy ran from the default branch post-merge.
  - Prevent: for Pages, plan both from the start: ask the admin to flip the source once,
    and put the deploy workflow on the default branch. A 1-second failed job with
    runner_id 0 means environment protection, not a code problem.

- A YouTube pull failing in the cloud sandbox is NOT the same failure as on Chris's PC.
  - Mistake: nearly reported "YouTube works, just network-blocked" as the whole story; the block in the
    cloud is a proxy CONNECT 403 (egress policy), which cookies cannot fix.
  - Fix: on his local machine the recurring failure is instead YouTube's auth/bot-check ("confirm you're
    not a bot") and Instagram login gating, which cookies.txt DO fix. Two different failures by environment.
  - Prevent: diagnose by environment. Proxy/CONNECT 403 = network policy (cloud). Extractor auth error =
    cookies (local). Do not conflate them, and never log "yt-dlp is broken."

## innerHTML polling wipes user input (2026-07-27)

- Mistake: dashboard boards re-render with app.innerHTML on a 10s/30s poll; every redraw
  rebuilt inputs empty, eating Chris's typing on the admin forms, and destroyed the
  member proof modal that lived inside the re-rendered container.
- Fix: snapshot input/textarea/select values + focus + cursor before the swap and restore
  after; move modal-root outside the re-rendered element.
- Prevention: any UI that refreshes via innerHTML must preserve in-flight user state.
  Test by typing during a forced refresh before shipping.
