---
name: topic
description: Topic stage of the content engine. Pick the single strongest angle for a brand and platform, grounded in Chris's real projects, and say in one line why it wins. Use when Chris has a few candidate angles and needs the best one chosen, or when content-pipeline runs the topic stage after scout.
---

# Topic

Angle selection. Second stage of the content engine (matches the Topic agent in the
command-center roster: "angle selection"). Takes a spark or the scout stage's candidates and
commits to the one angle worth building a post around.

## Inputs to ask for if missing

- Brand: Zenthra (Roblox guild) or Clearcoat Co. (auto detailing).
- Platform: TikTok, YouTube, or Instagram.
- A spark or candidate angles (from Chris, or from the `scout` stage). If none, run `scout` first.

## What to do

1. Weigh the candidate angles for this brand and platform.
2. Pick the strongest one. Ground it in Chris's real projects and details
   (memory-bank/projects.md), not a generic content idea.
3. Say in one line why it wins: the specific pattern, audience, or result it rides.

## Output

- The chosen angle, one line.
- Why it wins, one line.
- Hand it to the hook stage.

## Guardrails

- Draft only. Never posts, never DMs, never schedules.
- Specific over generic: real numbers, real detail, Chris's actual brands.
- Zenthra: multi-game Roblox guild, "Zenith of Power", competitive and community-driven.
- Clearcoat Co.: mobile waterless detailing, Void Black / Ice Blue, clean and results-first.
- Natural, non-AI voice. Never use "delve", "leverage", "fantastic", or em dashes.
- This is one worker stage; `content-pipeline` is the orchestrator that calls it in order.
