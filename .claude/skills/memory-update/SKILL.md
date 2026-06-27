---
name: memory-update
description: Run the memory-bank update ritual in one command. Refresh active-context and progress-log to reflect recent work, scan for banned words, then commit and push. Use at the end of meaningful work or when Chris says "update memory bank".
---

# Memory update

The one ritual that keeps the memory bank alive. Run it at the end of meaningful work.

## Steps

1. Read `memory-bank/README.md` for the current ritual and format.
2. Update `memory-bank/active-context.md`:
   - Rewrite the current-focus section to match what is actually true now.
   - Move finished items to done, drop stale ones, keep open threads honest.
3. Append a dated entry to `memory-bank/progress-log.md` (newest at the bottom, format `YYYY-MM-DD`).
   - One idea per line. Specific over vague. Reference PR numbers.
4. If identity, projects, career, preferences, or tools changed, edit that file too.
5. If a mistake or correction happened this session, append a lesson to `memory-bank/lessons.md`
   (mistake / fix / prevent), per `.claude/rules/learning.md`.

## Before committing (hard gate)

Scan every changed file for banned content:

```sh
grep -rnE '—|\bdelve\b|\bleverage\b|\bfantastic\b' $(git diff --name-only) 2>/dev/null
```

Fix every real hit (ignore lines that only quote the rule). Em dashes and the words
delve, leverage, fantastic are never allowed in committed prose.

## Commit and push

Branch off the default branch first (lessons.md: squash merges make stacked branches drift).
Commit with a clear message, push, open a PR, and merge it. Uncommitted memory is lost.

## Style

Short lines. One idea per line. No em dashes. No preamble. Match the existing files.
