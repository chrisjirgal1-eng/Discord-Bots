---
name: script
description: Script stage of the content engine. Draft a short-form script (about 15 to 40 seconds) from a hook: hook, 2 to 4 retention beats, then a close with one call to action. Spoken voice, short lines. Use when Chris has a hook and needs the full script, or when content-pipeline runs the script stage after hook.
---

# Script

Short-form drafts. Fourth stage of the content engine (matches the Script agent in the
command-center roster: "short-form drafts"). Turns a chosen hook into a script Chris can
record.

## Inputs to ask for if missing

- Brand: Zenthra (Roblox guild) or Clearcoat Co. (auto detailing).
- Platform: TikTok, YouTube, or Instagram.
- The hook to build on (from Chris, or from the `hook` stage).

## What to do

1. Open on the hook.
2. Write 2 to 4 retention beats: each keeps the viewer watching (a payoff, a turn, a proof,
   a fast how-to step). Short spoken lines, one idea per line.
3. Close with one clear call to action (join the Discord, book a detail, follow).
4. Target about 15 to 40 seconds of spoken time.

## Output

The script, ready to record: hook line, the beats, the close. Spoken voice, short lines. Hand
it to the caption stage (`caption` for Zenthra, `clearcoat-post` for Clearcoat).

## Guardrails

- Draft only. Never posts, never DMs, never schedules.
- Natural, non-AI voice. Never use "delve", "leverage", "fantastic", or em dashes.
- Specific over generic: real numbers, real detail, Chris's actual brands.
- Spoken, not written: it has to sound right read aloud.
- This is one worker stage; `content-pipeline` is the orchestrator that calls it in order.
