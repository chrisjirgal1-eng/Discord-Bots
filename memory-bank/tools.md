# Tools

External tools that make Claude work better on Chris's repos. Read on demand.

## graphify (code knowledge graph)

What it is: a code-intelligence tool. Parses a codebase with tree-sitter (25+
languages), builds a graph of how the code connects, clusters it into communities,
and lets Claude answer "how does X work" by querying the graph instead of reading
every file. Query cost is near zero. This is a direct token saver.

NOTE: this is a code knowledge graph, not a social-media content puller. The
`add <url>` and `clone` commands ingest source or docs from a URL into the corpus.
It does not pull feeds from TikTok, Instagram, etc.

### Setup (ephemeral sessions need this each time)

```
uv tool install graphifyy        # installs `graphify` and `graphify-mcp` on PATH
graphify install --platform claude   # installs the /graphify skill into Claude config
graphify update .                # build/refresh the graph, NO LLM, no API cost
```

Generated output lands in `graphify-out/` (gitignored). Rebuild anytime with
`graphify update .`.

### Daily-use commands

```
graphify query "<question>" --budget 1200   # BFS the graph for an answer, token-capped
graphify explain "<NodeName>"               # plain-language node + neighbors
graphify path "A" "B"                        # shortest path between two nodes
graphify affected "X"                         # reverse traversal, what depends on X
graphify watch .                              # rebuild on file changes
```

### Memory / feedback loop

- `graphify save-result --question Q --answer A --outcome useful|dead_end|corrected`
- `graphify reflect` aggregates outcomes into a deterministic LESSONS.md.

### How Claude should use it

When asked about this codebase's architecture or relationships, query the graph
first (or use the `/graphify` skill), then read only the files the graph points to.
Last semantic build on this repo: 83 nodes, 119 edges, 10 communities.
The graph (`graphify-out/graph.json`) and report are committed, so a fresh session
can query immediately after `uv tool install graphifyy`, no rebuild needed.

## claude-mem (automatic session memory)

What it is: automatic memory for Claude Code. Watches what Claude reads/edits/runs,
saves "observations," re-injects them in later sessions. Two-step retrieval:
`search(query, type, limit)` returns a lightweight index of IDs, then
`get_observations(ids=[...])` fetches full detail. Search, select, fetch. Token-efficient.

Install: `npx claude-mem install`. Start the worker: `npx claude-mem start`.
Stores everything in `~/.claude-mem` ON THE LOCAL MACHINE.

WHERE IT WORKS: local Claude Code on Chris's own computer. NOT cloud/web sessions.
The store is machine-local and the container wipes on reset, so it does not persist
across web sessions, and the worker/browser UI (localhost:37700) has no home in cloud.
For cloud sessions, the committed memory-bank/ is the durable memory instead.

## openclaw (self-hosted agent gateway)

What it is: a self-hosted gateway daemon that connects messaging channels (Discord,
Slack, etc.) to coding agents. Meant to run 24/7 on a persistent host.

Install: `npm install -g openclaw@latest` (or `pnpm add -g openclaw@latest`).

WHERE IT WORKS: a persistent machine, Chris's own computer or a small VPS. NOT cloud/web
sessions. `--install-daemon` stands up a background gateway service that dies when an
ephemeral container resets, and there is no stable host for channels to reach. Onboarding
also needs an auth provider, channel credentials, and a security model, so it is not safe
to auto-run unattended. Keep openclaw OUT of the cloud SessionStart hook.

Recommended non-interactive setup (run on the persistent host):

```
openclaw onboard \
  --non-interactive --accept-risk \
  --flow quickstart --mode local \
  --auth-choice claude-cli \
  --install-daemon --daemon-runtime node \
  --gateway-bind loopback --gateway-auth token \
  --skip-channels
```

Then add a channel and audit:

```
openclaw channels add        # pick Discord, paste bot token, set allowlist
openclaw security audit --deep
```

Notes: `--auth-choice claude-cli` reuses the existing Claude login (no separate API key).
`--gateway-bind loopback` keeps it reachable only from the host. Add channels after the
gateway is up so tokens and allowlists are set deliberately.

## SessionStart hook (cloud auto-setup)

`.claude/hooks/session-start.sh` runs at the start of every web session. It reinstalls
graphify and loads PATH so the tool and the committed graph are ready automatically.
The container resets each session; the hook re-assembles the setup in seconds.
Functionally permanent without manual steps. Active in the repo once merged to the default branch.

## Model routing

Convention for routing work across model tiers to save tokens without losing quality.
Full rule: `.claude/rules/model-routing.md` (always loaded, advisory).

Principle: frontier tokens buy judgment, mechanical work goes to the cheapest model that won't botch it.

Defaults applied automatically:
- Real coding work defaults to Sonnet 4.6.
- Search, discovery, and bulk mechanical edits go to Haiku subagents (also keeps the main context clean).
- Opus 4.8 only for design, hard debugging, and PR-grade review.
- Fable 5 reserved for genuinely hard, high-value problems.

The real control is the per-call `model` on Agent subagents (sonnet|opus|haiku|fable) and the `model` plus `effort` (low|medium|high|xhigh|max) on workflow agents. Frontmatter `model` is a hard override. The rule file is a nudge. The main session model stays Chris's choice, and do not switch it mid-session (it invalidates the prompt cache).

## Permissions (fewer prompts)

`.claude/settings.json` sets `defaultMode: bypassPermissions` by Chris's explicit request,
so tools run with no approval prompts. A deny-list still blocks catastrophic commands
(rm -rf /, rm -rf ~, mkfs, dd, fork bombs) because deny rules take precedence even in
bypass mode. The allow-list for common build commands is kept as documentation of the
expected toolset. To dial back, set `defaultMode` to `acceptEdits` (auto-accept edits,
prompt for other commands) or `default` (prompt for everything).

Caveat for web sessions: project settings apply at session launch and may be gated by the
environment's permission policy. If prompts still appear, set the permission mode for the
Claude Code web environment itself (the per-session/environment control), not just this file.

## VoltAgent subagents (154 specialists)

Marketplace `voltagent-subagents` from VoltAgent/awesome-claude-code-subagents. 154 specialist
subagents across 10 bundles: core-dev, lang, infra, qa-sec, data-ai, dev-exp, domains, biz,
meta, research. They appear as Agent tool types like `voltagent-core-dev:backend-developer`
or `voltagent-qa-sec:code-reviewer`, and register at session start.

Install note: `git clone` of third-party repos is blocked in this network, so the canonical
`claude plugin marketplace add VoltAgent/awesome-claude-code-subagents` fails with 403. The
working path (and what the SessionStart hook does) is to fetch the repo tarball with curl,
extract it to `~/.volt-subagents`, add that local directory as the marketplace, then
`claude plugin install <bundle>@voltagent-subagents` for each bundle. Auto-runs every web
session via `.claude/hooks/session-start.sh`.

How to use: route a task to the matching specialist via the Agent tool (e.g. a security pass
to `voltagent-qa-sec:code-reviewer`, a Discord/websocket feature to
`voltagent-core-dev:websocket-developer`). Pair this with the model-routing rule: pick the
specialist AND the right model tier.

## claude-video (watch streaming and video links)

Marketplace `claude-video` from bradautomates/claude-video. The `watch` plugin downloads a
video with yt-dlp, extracts frames, and transcribes with whisper, so a pasted video URL can
be analyzed. Invoke with `/watch <url-or-path>`.

Install path (git clone of third-party repos is 403-blocked, so use the tarball):
fetch `codeload.github.com/bradautomates/claude-video/tar.gz/refs/heads/main` with curl,
extract to `~/.claude-video-src`, `claude plugin marketplace add` that dir, then
`claude plugin install watch@claude-video`. Auto-runs every session via the SessionStart hook.

Dependencies (this container ships neither, the hook installs them):
- yt-dlp via `uv tool install yt-dlp`.
- ffmpeg via `pip install imageio-ffmpeg`, then symlink its static binary to `~/.local/bin/ffmpeg`.

Works on public streaming URLs that yt-dlp supports (YouTube, public reels, and similar).
It does NOT bypass login walls: a private Instagram saved collection or any auth-gated page
returns 403 and cannot be opened. For those, Chris pastes the public video links directly.
