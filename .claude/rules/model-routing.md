# Model routing

Advisory rule. Always loaded.
Goal: spend frontier tokens on judgment, push mechanical work down.
This saves cost without losing quality.

This file is context, not enforcement.
The main session model is Chris's choice, set with `/model`.
Do not switch the main model mid-session. It invalidates the prompt cache.
What this rule controls: the model and effort you pass to subagents and workflow agents.

## The one principle

Reasoning, architecture, and synthesis go to the biggest model.
Search, lookups, transforms, and boilerplate go to the smallest model that won't botch them.
Match the model to task altitude first. Then dial effort for cost vs quality.

Premium for the plan, cheaper for the build: when a task is worth the top tier, spend it on the
low-volume planning and architecture, then hand a tight plan down to the next tier for the bulk
build. The premium model barely costs on a short plan, and a high-volume build does not need it.
The catch is that the plan must be tight, or the cheaper model rethinks everything and the saving
disappears. (Source: reel DZc-ajJKT1L, pairs with prompt-first planning.)

## Default behavior (do this automatically, no need to ask Chris)

- Default real coding work to Sonnet 4.6.
- Delegate search, file discovery, and bulk mechanical edits to Haiku subagents.
- Escalate to Opus 4.8 only for design, hard debugging, or PR-grade review.
- Reserve Fable 5 for a genuinely hard, high-value problem.
- Delegating search to a Haiku subagent also keeps the main context window clean. Big win in ephemeral web sessions.

## Task to tier

| Task | Model |
|---|---|
| File search, code discovery, grep-style lookup, log parsing, simple classify | Haiku 4.5 |
| Bulk mechanical edit to an exact spec, format/lint fix, rename across files | Haiku 4.5 |
| Feature from a clear ticket, localized debugging, writing tests, pattern refactor | Sonnet 4.6 |
| Moderate tool loops: search, read, edit, run-tests | Sonnet 4.6 |
| Architecture, cross-subsystem debugging, correctness review, multi-step reasoning | Opus 4.8 |
| Long autonomous runs, the orchestrator seat that directs cheaper workers | Opus 4.8 |
| Frontier reasoning, overnight spec-to-system builds, the bug Opus keeps missing | Fable 5 |

Model IDs: Haiku 4.5 = `claude-haiku-4-5-20251001`. Sonnet 4.6 = `claude-sonnet-4-6`. Opus 4.8 = `claude-opus-4-8`. Fable 5 = `claude-fable-5`.

## How to route (the actual control)

Agent tool subagents take a per-call `model`: `sonnet | opus | haiku | fable` (or `inherit`, the default).
Workflow agents take the same `model` plus an `effort`: `low | medium | high | xhigh | max`.
A `model` in subagent frontmatter is a hard override. A line in this file is only a nudge, so put real routing in the subagent.

Two dials, set independently:
- Model = task altitude.
- Effort = how hard it thinks. Haiku has no effort. Sonnet defaults to high, drop to low/medium for scoped work. Opus defaults to xhigh, high is often enough.

## Guardrails

- Never route logic-bearing or irreversible work down. A too-small model returns a confident wrong answer and rarely flags doubt.
- Keep cheap models on read-only or well-bounded jobs. This is why built-in Explore runs on Haiku.
- Give every subagent a narrow spec and tell it exactly what to return, or the handoff drops the detail you needed.
- For a quick task, one pass on the current model beats orchestrating three workers. Delegate only when the side-work floods the main context or clearly doesn't need the big model.
- `/fast` is Opus-fast, not Opus-cheap. It speeds Opus output, it does not route down. Use it for latency, not savings.
