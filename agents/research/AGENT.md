# Research agent (scaffold)

Status: defined, NOT running. Turn on by enabling its workflow when you want it spending tokens.

Owns: deep dives and watching the field for things worth adding to Zoey. When live, it routes to
the EXISTING `deep-research` skill and the VoltAgent research bundle
(`voltagent-research:competitive-analyst`, `:trend-analyst`, `:search-specialist`), fetches
sources, adversarially verifies claims (verification.md), and writes a short, cited brief.

Escalates: a genuinely hard synthesis goes to Opus, and only the rarest to Fable 5. Findings that
imply a build go to the evolving loop as a backlog item, not an auto-change.

Reads/writes: the Research section of `agents/blackboard.md`.
