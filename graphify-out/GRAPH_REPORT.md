# Graph Report - .  (2026-06-27)

## Corpus Check
- Corpus is ~7,541 words - fits in a single context window. You may not need a graph.

## Summary
- 83 nodes · 119 edges · 10 communities (6 shown, 4 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.7)
- Token cost: 0 input · 56,510 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Audio & Queue Management|Audio & Queue Management]]
- [[_COMMUNITY_Chris Business & Identity Context|Chris Business & Identity Context]]
- [[_COMMUNITY_Music Bot Voice Lifecycle|Music Bot Voice Lifecycle]]
- [[_COMMUNITY_Bot Slash Commands|Bot Slash Commands]]
- [[_COMMUNITY_Memory Bank Ops & Projects|Memory Bank Ops & Projects]]
- [[_COMMUNITY_ClearCoat Sheets Backend|ClearCoat Sheets Backend]]
- [[_COMMUNITY_Vercel Deploy Config|Vercel Deploy Config]]
- [[_COMMUNITY_MCP Connectors & Access|MCP Connectors & Access]]
- [[_COMMUNITY_Memory Export Format|Memory Export Format]]
- [[_COMMUNITY_Build Approval Protocol|Build Approval Protocol]]

## God Nodes (most connected - your core abstractions)
1. `Track` - 11 edges
2. `MusicBot` - 10 edges
3. `GuildQueue` - 10 edges
4. `Persistent Memory Bank` - 9 edges
5. `QueueManager` - 8 edges
6. `fetch_tracks()` - 4 edges
7. `cmd_play()` - 4 edges
8. `doGet()` - 4 edges
9. `Memory Bank Update Ritual` - 4 edges
10. `Chris (Zenthra)` - 4 edges

## Surprising Connections (you probably didn't know these)
- `MusicBot` --uses--> `QueueManager`  [INFERRED]
  bot.py → queue_manager.py
- `GuildQueue` --uses--> `Track`  [INFERRED]
  queue_manager.py → audio.py
- `QueueManager` --uses--> `Track`  [INFERRED]
  queue_manager.py → audio.py
- `cmd_play()` --calls--> `fetch_tracks()`  [EXTRACTED]
  bot.py → audio.py
- `Persistent Memory Bank` --references--> `Active Context`  [EXTRACTED]
  CLAUDE.md → memory-bank/active-context.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Auto-loaded Every Session Memory Set** — memory_bank_instructions_instructions, memory_bank_identity_chris, memory_bank_preferences_preferences, memory_bank_active_context_active_context, claude_memory_bank [EXTRACTED 1.00]
- **ClearCoat Booking and Tracking Flow** — clearcoatco_website_index, clearcoatco_website_calendly_booking, clearcoatco_website_apps_script_backend, clearcoatco_website_service_tiers [EXTRACTED 1.00]
- **Chris's Active Venture Portfolio** — memory_bank_projects_zenthra, memory_bank_projects_clearcoat_co, memory_bank_projects_kos, memory_bank_projects_jarvis [INFERRED 0.85]

## Communities (10 total, 4 thin omitted)

### Community 0 - "Audio & Queue Management"
Cohesion: 0.16
Nodes (4): fetch_tracks(), Track, GuildQueue, QueueManager

### Community 1 - "Chris Business & Identity Context"
Cohesion: 0.16
Nodes (16): Persistent Memory Bank, Google Apps Script Sheet Backend, Calendly Booking Widget, ClearCoat Co. Website (index.html), Service Tier Pricing, Coach Outreach Emails, D1 Track and Field Recruitment, Chris (Zenthra) (+8 more)

### Community 2 - "Music Bot Voice Lifecycle"
Cohesion: 0.24
Nodes (6): MusicBot, Guild, Lock, Member, VoiceClient, VoiceState

### Community 3 - "Bot Slash Commands"
Cohesion: 0.29
Nodes (11): cmd_leave(), cmd_nowplaying(), cmd_pause(), cmd_play(), cmd_queue(), cmd_resume(), cmd_skip(), cmd_stop() (+3 more)

### Community 4 - "Memory Bank Ops & Projects"
Cohesion: 0.24
Nodes (10): Token-Conserving Output Style, Memory Bank Update Ritual, Active Context, Progress Log, JARVIS (Personal AI OS), Knowledge Operating System (KOS), Zenthra Production Discord Bot, Auto-load vs On-demand Split (+2 more)

### Community 5 - "ClearCoat Sheets Backend"
Cohesion: 0.70
Nodes (4): doGet(), getData(), logJob(), submitReview()

## Knowledge Gaps
- **9 isolated node(s):** `outputDirectory`, `rewrites`, `Memory Bank (README)`, `Memory Export Format`, `Instructions (Rules from Chris)` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MusicBot` connect `Music Bot Voice Lifecycle` to `Audio & Queue Management`, `Bot Slash Commands`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `QueueManager` connect `Audio & Queue Management` to `Music Bot Voice Lifecycle`, `Bot Slash Commands`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Track` (e.g. with `GuildQueue` and `QueueManager`) actually correct?**
  _`Track` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `outputDirectory`, `rewrites`, `Memory Bank (README)` to the rest of the system?**
  _13 weakly-connected nodes found - possible documentation gaps or missing edges._