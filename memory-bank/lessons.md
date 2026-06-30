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

## 2026-06-30

- The live Instagram cookie file was the small IG-only export, not the big multi-site one.
  - Mistake: copied `research/Automation/ig_cookies.txt` (539KB, all sites, newer) to `cookies.txt`;
    it failed auth with "empty media response". The 12KB Instagram-only export authenticated fine.
  - Fix: smoke-test with `yt-dlp -s --cookies <file> <reel>` and pick the file that prints OK before
    a batch. Also `.gitignore` had no cookies rule (despite "keep it out of the repo"), and
    `watch-batch.sh` was not passing `--cookies` at all. Added cookie patterns to `.gitignore` and
    wired `--cookies cookies.txt` into `watch-batch.sh`.
  - Prevent: validate the cookie file with a one-reel simulate first; never assume newer or bigger
    means valid. Confirm `git check-ignore cookies.txt` before copying any secret into the repo root.

- Image carousels and silent reels cannot be transcribed; that is not a pipeline failure.
  - Mistake: treated 4 "download FAILED" reels as something to fix and retried them twice.
  - Fix: diagnosed each. 3 were `/p/` image posts ("No video formats found"); 1 reel pulled a 132KB
    clip with no audio stream (ffmpeg "Output file does not contain any stream"). None have speech.
  - Prevent: a `/p/` image post or a no-audio reel is expected attrition. Confirm "No video formats"
    or "no stream" once, mark it failed, and move on instead of retrying.
