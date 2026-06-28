# Graph Report - Discord-Bots  (2026-06-27)

## Corpus Check
- 45 files · ~31,907 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 400 nodes · 545 edges · 39 communities (33 shown, 6 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 38 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `796c9354`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]

## God Nodes (most connected - your core abstractions)
1. `GuildQueue` - 42 edges
2. `Track` - 40 edges
3. `QueueManager` - 25 edges
4. `TestGuildQueue` - 18 edges
5. `TestBotCommandLogic` - 14 edges
6. `_make_track()` - 14 edges
7. `Active Context` - 13 edges
8. `fetch_tracks()` - 10 edges
9. `MusicBot` - 10 edges
10. `TestTrack` - 10 edges

## Surprising Connections (you probably didn't know these)
- `GuildQueue` --uses--> `Track`  [INFERRED]
  queue_manager.py → audio.py
- `QueueManager` --uses--> `Track`  [INFERRED]
  queue_manager.py → audio.py
- `TestAutoJoinLogic` --uses--> `Track`  [INFERRED]
  tests/test_bot.py → audio.py
- `TestBotCommandLogic` --uses--> `Track`  [INFERRED]
  tests/test_bot.py → audio.py
- `TestMusicBotLock` --uses--> `Track`  [INFERRED]
  tests/test_bot.py → audio.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Auto-loaded Every Session Memory Set** — memory_bank_instructions_instructions, memory_bank_identity_chris, memory_bank_preferences_preferences, memory_bank_active_context_active_context, claude_memory_bank [EXTRACTED 1.00]
- **ClearCoat Booking and Tracking Flow** — clearcoatco_website_index, clearcoatco_website_calendly_booking, clearcoatco_website_apps_script_backend, clearcoatco_website_service_tiers [EXTRACTED 1.00]
- **Chris's Active Venture Portfolio** — memory_bank_projects_zenthra, memory_bank_projects_clearcoat_co, memory_bank_projects_kos, memory_bank_projects_jarvis [INFERRED 0.85]

## Communities (39 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (9): QueueManager, Test the auto-join decision logic., Simulating the max() logic from _auto_join., Test the reconnection tracking set logic., Test the play_next logic flow without needing a real VoiceClient., TestAutoJoinLogic, TestPlayNextLogic, TestReconnectionLogic (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (43): Persistent Memory Bank, Token-Conserving Output Style, Memory Bank Update Ritual, Google Apps Script Sheet Backend, Calendly Booking Widget, ClearCoat Co. Website (index.html), Service Tier Pricing, Active Context (+35 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (30): cmd_leave(), cmd_nowplaying(), cmd_pause(), cmd_play(), cmd_queue(), cmd_resume(), cmd_skip(), cmd_stop() (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.10
Nodes (11): GuildQueue, The /stop command clears queue and stops playback., The /skip logic: vc.stop() triggers after_cb which calls play_next., When nothing is playing, current is None., Test the queue formatting logic from /queue command., The /leave command clears queue before disconnecting., Test command logic patterns used in bot.py without actual Discord interactions., Volume command logic: level / 100 applied to queue. (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (5): fetch_tracks(), Track, TestConstants, TestFetchTracks, TestTrack

### Community 5 - "Community 5"
Cohesion: 0.57
Nodes (7): doGet(), getData(), getDataRows(), getSheet(), logJob(), sanitize(), submitReview()

### Community 8 - "Community 8"
Cohesion: 0.14
Nodes (12): Analysis style, Before any build or code task, Instructions, Memory export format, When Chris pastes a doc, report, or transcript, When debugging, Writing and content, Layout (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (13): claude-mem (automatic session memory), claude-video (watch streaming and video links), Daily-use commands, graphify (code knowledge graph), How Claude should use it, Memory / feedback loop, Model routing, openclaw (self-hosted agent gateway) (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.17
Nodes (11): 1. Executive summary, 2. What my autonomous potential actually is, 3. ARIS patterns worth stealing, 4. Capability inventory and honest limits, 5. Prioritized roadmap, 6. The 3 likeliest failure points, 7. One thing to do first, Autonomous Potential: The Plan (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.20
Nodes (9): Done looks like, Guardrails, JARVIS kickoff, Make Chris look good (the cool stuff), Phase 0: setup, Phase 1: transcribe (mechanical), Phase 2: digest, goals first, Phase 3: apply the real techniques (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (8): Budget caps are hard ceilings, Gate before shipping, How to apply it here, Loops need four exits, Memory hygiene, The one law, Type-A vs Type-B, Verification discipline

### Community 14 - "Community 14"
Cohesion: 0.43
Nodes (6): download_audio(), ffmpeg_path(), load_env(), main(), transcribe(), vid_id()

### Community 15 - "Community 15"
Cohesion: 0.25
Nodes (7): 1. Global (your computer, all projects), 2. Per-repo (another project, including cloud sessions), Process videos in bulk (the fix for the Instagram wall), Take this setup anywhere, The honest caveat, Two ways to install, What is portable vs not

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (7): ALREADY-HAVE (confirm, do not rebuild), HYPE or off-target (skipped, logged honestly), NEW, high-value (apply these), TECHNIQUES, The goal (north star), in 5 lines, What gets applied in Phase 3, Worth noting, optional (not applied now)

### Community 17 - "Community 17"
Cohesion: 0.29
Nodes (6): Brand, Clearcoat Co. post, Guardrail, Inputs to ask for if missing, Output, Voice rules (hard)

### Community 18 - "Community 18"
Cohesion: 0.29
Nodes (6): Coach outreach email, Guardrail, Inputs to ask for if missing, Output, Structure, Voice rules (hard)

### Community 19 - "Community 19"
Cohesion: 0.29
Nodes (6): Apply, do not just list, Digest transcripts, Honesty, Input, Steps, The goal videos come first

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (6): Applied 2026-06-27 (Chris said "add everything"), Discord music bot: code review, Fixed this pass (safe, isolated, no concurrency change), How to proceed, Low priority, Original findings (for reference)

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (6): Architecture in one read, Capability map, JARVIS, Talk to it, What needs Chris before it is real, What runs locally today

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (6): Guardrails (always), How to route a request, JARVIS, Routing table, The one rule that makes it JARVIS, not a dashboard, Voice and 24/7 (specced, not yet wired)

### Community 23 - "Community 23"
Cohesion: 0.29
Nodes (6): 1. Think before coding, 2. Simplicity first, 3. Surgical changes, 4. Goal-driven execution, Coding discipline, Working

### Community 24 - "Community 24"
Cohesion: 0.29
Nodes (6): Default behavior (do this automatically, no need to ask Chris), Guardrails, How to route (the actual control), Model routing, Task to tier, The one principle

### Community 25 - "Community 25"
Cohesion: 0.67
Nodes (5): install-claude-setup.sh script, copy_rules_and_skills(), die(), install_global(), install_repo()

### Community 26 - "Community 26"
Cohesion: 0.33
Nodes (5): Brand notes, Caption, Inputs to ask for if missing, Output, Voice rules (hard)

### Community 27 - "Community 27"
Cohesion: 0.33
Nodes (5): Auto-loaded every session, Output style (conserve tokens), Read on demand (not auto-loaded, saves context), The one ritual that keeps this alive, Working with Chris

### Community 28 - "Community 28"
Cohesion: 0.33
Nodes (5): Handoff, Resuming, Steps, When to run, Why committed, not local

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (5): Before committing (hard gate), Commit and push, Memory update, Steps, Style

### Community 30 - "Community 30"
Cohesion: 0.33
Nodes (5): Honest limit, Hygiene, Learning loop, The loop, What counts as a lesson

### Community 31 - "Community 31"
Cohesion: 0.33
Nodes (5): Guardrail, Inputs to ask for if missing, Output, Voice rules (hard), Zenthra announcement

### Community 32 - "Community 32"
Cohesion: 0.40
Nodes (4): Assets built, Career, D1 track and field recruitment, Voice rules for recruitment

### Community 33 - "Community 33"
Cohesion: 0.40
Nodes (4): Identity, Personal, The name, Who Chris is

### Community 34 - "Community 34"
Cohesion: 0.40
Nodes (4): Speed never skips the gate, The five speed habits, The honest rate, Throughput

## Knowledge Gaps
- **151 isolated node(s):** `session-start.sh script`, `PATH`, `watch-batch.sh script`, `outputDirectory`, `rewrites` (+146 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Track` connect `Community 4` to `Community 0`, `Community 2`, `Community 3`, `Community 14`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `QueueManager` connect `Community 0` to `Community 2`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `GuildQueue` connect `Community 3` to `Community 0`, `Community 2`, `Community 4`, `Community 14`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `GuildQueue` (e.g. with `Track` and `TestAutoJoinLogic`) actually correct?**
  _`GuildQueue` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Track` (e.g. with `GuildQueue` and `QueueManager`) actually correct?**
  _`Track` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `QueueManager` (e.g. with `MusicBot` and `Track`) actually correct?**
  _`QueueManager` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `TestGuildQueue` (e.g. with `Track` and `GuildQueue`) actually correct?**
  _`TestGuildQueue` has 3 INFERRED edges - model-reasoned connections that need verification._