---
name: content-pipeline
description: Run Chris's content pipeline end to end as named stages (scout, topic, hook, script, caption) and produce a review-ready draft package. Use when Chris says "run the content pipeline", "make me content for Zenthra/Clearcoat", or wants a full post draft (hook, script, and caption together). For a caption only, use the caption or clearcoat-post skill instead. Draft only, never posts.
---

# Content pipeline

The goal videos show a content engine run by named specialist agents with one chat to drive
them (DZ_xzicxQPx, and the goal reel that posts at scale). This is that pipeline, built from
the skills that already exist. It takes a brand and a spark and returns a finished draft
package Chris can review and post. It never posts on its own.

## Inputs to ask for if missing

- Brand: Zenthra (Roblox guild) or Clearcoat Co. (auto detailing).
- Platform: TikTok, YouTube, or Instagram.
- A spark: a topic, a clip, a result, or "find me one" (then the scout stage picks).

## The stages (run in order, show each)

1. **Scout** (optional). If Chris has no topic, scan what is working in the niche. Use web
   search read-only: trending Roblox angles for Zenthra, local detailing hooks for Clearcoat.
   Return 3 to 5 candidate angles. Read-only, never logs in or posts.
2. **Topic**. Pick the strongest angle for the brand and platform, grounded in Chris's real
   projects (memory-bank/projects.md), not generic. One line on why it wins.
3. **Hook**. Write 3 first-three-second hooks for that angle. Curiosity or stakes in the first
   line, the way the strongest reels open. Label the sharpest.
4. **Script**. Draft the short-form script (about 15 to 40 seconds): hook, then 2 to 4 retention
   beats, then a close with one call to action. Spoken voice, short lines.
5. **Caption**. Route to the `caption` skill for Zenthra, or `clearcoat-post` for Clearcoat, to
   get 3 caption versions with hashtags. Do not rewrite those skills, call them.

## Output: the draft package

Return one tidy package:
- Angle (one line) and why.
- Hook options (3), strongest labeled.
- Script (ready to record).
- Caption (the best version from the routed skill) plus 2 alternates.
- A one-line next step for Chris (record this, or pick a hook and rerun the script).

## Voice rules (hard)

- Natural, non-AI voice. Never use "delve", "leverage", "fantastic", or em dashes.
- Specific over generic: real numbers, real detail, Chris's actual brands.
- Zenthra: multi-game Roblox guild, "Zenith of Power", competitive and community-driven.
- Clearcoat Co.: mobile waterless detailing, Void Black / Ice Blue, clean and results-first.
- Make it look like a sharp real creator made it, not a template.

## Guardrails

- Draft only. Never post, never DM, never schedule. Chris reviews and posts himself.
- Scout is read-only web search. No logins, no scraping behind auth, no outbound actions.
- This is the worker pipeline; the `jarvis` skill is the front door that routes here.
