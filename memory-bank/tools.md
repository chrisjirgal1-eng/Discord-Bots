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

## SessionStart hook (cloud auto-setup)

`.claude/hooks/session-start.sh` runs at the start of every web session. It reinstalls
graphify and loads PATH so the tool and the committed graph are ready automatically.
The container resets each session; the hook re-assembles the setup in seconds.
Functionally permanent without manual steps. Active in the repo once merged to the default branch.
