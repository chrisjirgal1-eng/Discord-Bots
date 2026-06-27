# Learning loop

Advisory rule. Always loaded. The self-improvement mechanism for this setup.
Goal: stop repeating the same coding mistakes across sessions.

Based on Reflexion: an agent improves by writing a short post-mortem after a mistake,
saving it to memory, and reading that memory before acting again. No retraining.
The learning lives in committed files, so it survives a session reset.

## The loop

1. Before similar work, consult `memory-bank/lessons.md`. It is the anti-repetition memory.
2. When I make a mistake, get corrected, or a fresh reviewer catches something, write a lesson.
3. A lesson is three lines: the mistake, the fix, the prevention rule.
4. Append it to `memory-bank/lessons.md`, commit, and push. Uncommitted learning is lost.

## What counts as a lesson

- A real error I hit and fixed (a 403, a wrong path, a bad assumption, a missed rule).
- A correction from Chris or from a reviewer.
- A non-obvious workaround that took more than one try.

Not a lesson: a one-off typo I caught instantly, or restating something already in lessons.

## Hygiene

- Store the fix and the prevention, never "X tool is broken." A 403 today is not a permanent truth.
- Keep `lessons.md` deduped and concise. Merge near-duplicates. Drop lessons that became stale.
- If a lesson generalizes into a standing rule, promote it to a `.claude/rules/` file instead.

## Honest limit

This does not change my weights. It changes what I read before acting.
That is enough to stop the same mistake twice, which is the whole point.
