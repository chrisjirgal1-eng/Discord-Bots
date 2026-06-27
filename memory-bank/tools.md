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
Last build on this repo: 104 nodes, 126 edges, 14 communities.
