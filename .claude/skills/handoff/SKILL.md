---
name: handoff
description: Write a clean continuation doc before ending or clearing a session mid-task, so a fresh agent resumes exactly where this one left off. Use when a task is unfinished and the context is getting long, debugging is going in circles, or before /clear. Distinct from memory-update, which records durable project state.
---

# Handoff

The longer a session runs, the more it carries forward bad assumptions and dead debugging
paths. Compaction keeps that shape. A clean handoff does not: it hands a fresh agent the
goal and the current state, nothing else. Source: the videos call this the single best fix
for context rot (DYNWWdiMiH7).

Use this for an UNFINISHED task. For durable project memory at the end of finished work,
use the `memory-update` skill instead. The two are different jobs.

## When to run

- A task is mid-flight and the context window is getting long or muddled.
- Claude keeps trying the same fix that does not work.
- Chris is stepping away and wants to resume later or in a fresh session.

## Steps

1. Write or overwrite `memory-bank/handoff.md` with these sections, short lines, one idea per line:
   - **Goal**: the one outcome this task must reach, with its done condition.
   - **State now**: what is true right now, what works, what is committed vs uncommitted.
   - **Files in flight**: exact paths being changed, and what each change is for.
   - **Tried and failed**: approaches already ruled out, so the next agent does not repeat them.
   - **Next step**: the single concrete action to take next, and how to verify it.
   - **Branch**: the working branch, so the next agent does not stack on a squash-merged one.
2. Keep it under one screen. If it is longer, the task is too big; name the next slice only.
3. Scan for banned content before committing:
   ```sh
   grep -rnE '—|\bdelve\b|\bleverage\b|\bfantastic\b' memory-bank/handoff.md
   ```
4. Commit and push `memory-bank/handoff.md` so it survives a session reset (the whole point).

## Resuming

A fresh session: read `memory-bank/handoff.md` first, confirm the state still holds, then
continue from Next step. When the task is done, clear the file to a single line
(`No handoff in flight.`) and commit, so a stale handoff never misleads a later session.

## Why committed, not local

Ephemeral cloud sessions lose anything uncommitted. A handoff that is not pushed is gone
the moment the session ends, which defeats the purpose. Commit it like the rest of the
memory bank.
