# Zoey's autonomous agents

Separate, long-lived agents that each work their own domain for Zoey and report back, so she
keeps getting stronger on her own. Deliberately lean: no CrewAI / LangGraph / database. The
"blackboard" is a committed file, the agents are charters + the existing skills/subagents, and
they run on GitHub Actions (free, 24/7). This reuses what already exists; it does not rebuild it.

## How it works

- **Blackboard** (`agents/blackboard.md`): the shared state file. Each agent reads only its own
  section and writes its findings + last action there. Git-versioned, token-cheap, no DB.
- **Each agent** is a folder with an `AGENT.md` charter: what it owns, what tools/skills it uses,
  its schedule, and how it escalates a hard call to the evolving loop. An agent never duplicates
  logic that already exists; it routes to the skills (`.claude/skills/`) and the 154 VoltAgent
  subagents.
- **The evolving loop** (`.github/workflows/zoe-evolve.yml`) is the supervisor: on a schedule it
  reads the blackboard + the security findings + the backlog (`memory-bank/handoff.md`), does ONE
  verified improvement, appends a lesson (`memory-bank/lessons.md`), updates the blackboard, and
  opens a PR. It never pushes to the default branch unattended.
- **Token discipline** (reuse `.claude/rules/model-routing.md`): routing/loop body on Haiku, real
  work on Sonnet, escalate to Opus for hard reasoning, and to Fable 5 only for the rare hardest
  step. Verification gate from `.claude/rules/verification.md` (the writer never grades its own
  work; loops exit on quality / cap / budget / no-progress).

## The agents

| Agent | Folder | Status | Owns |
|---|---|---|---|
| Security | `agents/security/` | **live** (free scanners, no API key) | deps, secrets, SAST, hardening |
| Content | `agents/content/` | scaffold (charter only) | Zenthra + Clearcoat drafts via the content skills |
| Research | `agents/research/` | scaffold | deep-research + competitive/trend VoltAgents |
| Ops | `agents/ops/` | scaffold | machine/repo health via read_file/run_command + infra agents |

Security is wired first (per Chris). The others are defined, not running, so each can be turned on
later by enabling its workflow. Turn one on only when you want it spending time/tokens.
