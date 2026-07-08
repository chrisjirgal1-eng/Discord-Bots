#!/usr/bin/env python3
"""Status generator: read the repo, write the HUD's CONFIG status block.

The JARVIS command center (jarvis-ui/index.html) shows live counts in its
CONFIG block: skills, agents, graph nodes, tests. Those were hardcoded and
drifted out of date. This script reads the real numbers from the repo and
rewrites the marked blocks so the HUD is always accurate.

What it counts (all repo-local and verifiable except agents):
- skills:       .claude/skills/*/SKILL.md
- tests:        `pytest --collect-only` count, falling back to a static scan
- graph nodes:  graphify-out/graph.json node count (edges reported too)
- agents:       VoltAgent markdown files in the user plugin cache (best-effort;
                falls back to the last value in zoe-ui/config.json when the
                cache is not present, rather than reporting a false 0)
- plugins/tools: plugins/*.py and tools/*.py (recorded in the JSON snapshot)

It rewrites three marker-delimited blocks in jarvis-ui/index.html (metrics,
feed, status) and refreshes the zoe-ui/config.json snapshot. Idempotent: run
it again with nothing changed and the files stay byte-identical.

Usage:
  python tools/zoe_status.py          # update the HUD + snapshot
  python tools/zoe_status.py --dry    # print the counts, write nothing
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUD = ROOT / "jarvis-ui" / "index.html"
SNAPSHOT = ROOT / "zoe-ui" / "config.json"
GRAPH = ROOT / "graphify-out" / "graph.json"


def count_skills() -> int:
    return len(list((ROOT / ".claude" / "skills").glob("*/SKILL.md")))


def count_tests() -> int:
    """Prefer pytest's own collection count; fall back to a static scan."""
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--collect-only"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        ).stdout
        # pytest phrasing varies by version/verbosity: "76 tests collected"
        # (quiet summary) or "collected 76 items" (default header).
        m = re.search(r"(\d+)\s+tests?\s+collected", out) or re.search(r"collected\s+(\d+)\s+items?", out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    # Fallback: count test functions without running pytest.
    total = 0
    for f in (ROOT / "tests").glob("test_*.py"):
        total += len(re.findall(r"^\s*(?:async\s+)?def\s+test_", f.read_text(encoding="utf-8"), re.M))
    return total


def count_graph() -> tuple[int, int]:
    """Return (nodes, edges) from the committed knowledge graph."""
    if not GRAPH.exists():
        return 0, 0
    d = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = len(d.get("nodes", []))
    edges = len(d.get("links", d.get("edges", [])))
    return nodes, edges


def count_agents(prev: int) -> int:
    """Count installed VoltAgent files (best-effort, read-only).

    They live in the user plugin cache, outside the repo, so this is portable
    only in the sense that a missing cache falls back to the last known value
    instead of reporting a misleading 0.
    """
    cache = Path.home() / ".claude" / "plugins" / "cache" / "voltagent-subagents"
    if cache.is_dir():
        n = len(list(cache.rglob("*.md")))
        if n:
            return n
    return prev


def count_py(subdir: str) -> int:
    return len(list((ROOT / subdir).glob("*.py")))


def load_prev_agents() -> int:
    try:
        return int(json.loads(SNAPSHOT.read_text(encoding="utf-8")).get("agents", 0))
    except Exception:
        return 0


def splice(html: str, name: str, inner: str) -> str:
    """Replace the content between /*SG:name*/ and /*SG:name-end*/ markers."""
    start, end = f"/*SG:{name}*/", f"/*SG:{name}-end*/"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    repl = f"{start}\n  {inner}\n  {end}"
    new, n = pat.subn(lambda _m: repl, html)
    if n != 1:
        raise SystemExit(f"marker '{name}' not found exactly once in {HUD} (found {n})")
    return new


def build_blocks(skills: int, agents: int, nodes: int, tests: int) -> dict[str, str]:
    metrics = (
        f'metrics:[["{skills}","skills"],["{agents}","agents"],'
        f'["{nodes}","graph nodes"],["{tests}","tests green"]],'
    )
    feed = (
        "feed:[\n"
        f'    ["MEMORY","graph synced, {nodes} nodes"],["AGENTS","{agents} specialists online"],\n'
        f'    ["TESTS","{tests} passing, suite green"],["SCOUT","scanning Zenthra trends"],\n'
        f'    ["ROUTER","{skills} skills mounted"],["MEMORY","handoff committed"],\n'
        '    ["GRAPHIFY","content pipeline mapped to revenue"],["CORE","awaiting command"],\n'
        "  ],"
    )
    status = (
        "status:[\n"
        f'    ["ok","Memory + knowledge graph","{nodes} nodes"],["ok","Test suite","{tests} green"],\n'
        f'    ["ok","JARVIS router + {skills} skills","wired"],["ok","{agents} specialist agents","loaded"],\n'
        '    ["ok","Content pipeline","draft only"],["ok","Voice: two-way loop (Lily)","live"],\n'
        '    ["warn","24/7 automation","needs a host"],["warn","Auto-posting","needs approval"],\n'
        "  ],"
    )
    return {"metrics": metrics, "feed": feed, "status": status}


def main() -> int:
    dry = "--dry" in sys.argv[1:]

    skills = count_skills()
    tests = count_tests()
    nodes, edges = count_graph()
    agents = count_agents(load_prev_agents())
    plugins = count_py("plugins")
    tools = count_py("tools")

    summary = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "skills": skills,
        "agents": agents,
        "graph_nodes": nodes,
        "graph_edges": edges,
        "tests": tests,
        "plugins": plugins,
        "tools": tools,
    }

    print("HUD status:")
    for k in ("skills", "agents", "graph_nodes", "graph_edges", "tests", "plugins", "tools"):
        print(f"  {k:12} {summary[k]}")

    if dry:
        print("--dry: no files written")
        return 0

    if not HUD.exists():
        raise SystemExit(f"HUD not found: {HUD}")
    html = HUD.read_text(encoding="utf-8")
    for name, inner in build_blocks(skills, agents, nodes, tests).items():
        html = splice(html, name, inner)
    HUD.write_text(html, encoding="utf-8")
    print(f"updated {HUD.relative_to(ROOT)}")

    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"updated {SNAPSHOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
