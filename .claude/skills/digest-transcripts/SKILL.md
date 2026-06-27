---
name: digest-transcripts
description: Read video transcripts (from tools/watch-batch.sh) and turn them into a ranked "techniques to apply" list, then apply the genuinely useful ones to the setup. Use after transcripts land in transcripts/.
---

# Digest transcripts

Turn a folder of video transcripts into setup upgrades. The transcripts come from
`tools/watch-batch.sh` (download + Whisper, run on Chris's machine). This skill is the
judgment half: extract what is worth applying, skip the hype, apply the real upgrades.

## Input

A directory of `.txt` transcripts (default `transcripts/`). Files starting with `__FAILED__`
are skipped (the download or transcribe failed for that video).

## The goal videos come first

Three transcripts are the north star, the "become the true Claude" targets (pinned at the
top of `tools/video-urls.txt`): `DZlQ7GZnJR7`, `DZu4FFeDtIH`, `DZVEN4gMRXV`. Read and
understand these FIRST. They define what the end state looks like. Then judge every training
video against that goal: a technique earns its place only if it moves the setup toward what
the goal videos describe. Capture the goal in 3 to 5 lines at the top of TECHNIQUES.md.

## Steps

1. Read the three goal transcripts first, then the rest. For large batches, fan out: a Haiku
   subagent per chunk extracts the technique(s) from its files and returns structured notes
   (per model-routing.md). Keep the main context clean.
2. For each video, capture: the core technique in one line, the specific claim, and whether it
   applies to Chris's Claude Code setup.
3. Dedupe hard against what already exists: the rules (model-routing, verification, learning,
   coding-discipline, throughput), the skills, the memory bank, graphify, the 154 subagents.
   A technique already covered is "already have", not a new action.
4. Write `transcripts/TECHNIQUES.md`: a ranked table with columns
   technique | source (video id) | value (high/med/low) | status (new / already have / hype) | action.

## Apply, do not just list

For each NEW, high-value technique:
- Propose the concrete setup change (a new skill, a rule edit, a workflow, a config).
- Keep it simple (coding-discipline.md): no speculative abstractions, only what the technique earns.
- Route the "is this real and worth it" judgment to a fresh subagent (verification.md). Social
  reels overhype; many techniques are wrong, dated, or already standard. Apply only what survives.
- Commit each applied change via a branch off the default branch, scan for banned words first.
- Append a lesson to memory-bank/lessons.md if a transcript corrected a wrong assumption.

## Honesty

Separate verified-useful from hype. Say plainly which techniques were skipped and why.
Do not add a rule or skill just because a video said so. The bar is: does it measurably
improve the setup beyond what is already there.
