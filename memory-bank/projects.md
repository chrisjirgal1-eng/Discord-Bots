# Projects

Status as of 2026-06-27. Update when state changes.

## Zenthra (multi-game Roblox guild)

- 1,300+ Discord members.
- Games: Cursed Blade, Sailor Piece, Universal Tower Defense, Grow a Garden 2.
- Tagline: "Zenith of Power."
- Production Discord bot built with discord.py + Claude API (claude-sonnet-4-6).
  Multi-file architecture with cogs: moderation, roles, announcements, AI chat.
- A Discord music bot also lives in this repo: `bot.py`, `audio.py`, `queue_manager.py`.
  Persistent, auto-join, slash commands.
- Member tracker: multi-version Google Sheets-compatible Excel for ~135 members.
  Tracks bounty, NPC kills, boss kills, playtime, dungeons, rare drops, sea beasts,
  world bosses, join date, last online. Color-coded activity and role-based row highlights.
- Server build-out done: Ticket Tool verification, Carl-bot reaction roles/triggers,
  MEE6 + Arcane leveling (15-25 XP/msg, 60s cooldown, 20 nautical roles every 5 levels
  from Castaway to Poseidon), GiveawayBot, Bloxlink, AutoMod, co-owner agreement.
- Role audit flagged: Administration had Administrator toggle on; Manage Server inversion across ranks.
- Discord access works via Zapier. Raw requests to /channels/{id}/messages work.
  Guild-level admin endpoints return 403.

## Clearcoat Co. (mobile waterless auto detailing)

- Waterless detailing using Optimum No Rinse.
- Brand palette: Void Black, Carbon, Ice Blue, Chrome.
- 4 service tiers: Interior Only, Quick Shine, Full Detail, Premium.
- Free tool stack: Calendly, Beacons.ai, PayPal, Zelle.
- Content on TikTok and Instagram.
- Website lives in this repo at `clearcoatco-website/` (index.html, Google Apps Script
  booking, vercel.json for static deploy). Has Google Sheets auto-tracking.
- TikTok business verified as sole proprietor. Accepted EIN doc is the IRS 147C letter, not CP575.

## Knowledge Operating System (KOS)

- Self-hosted TypeScript platform. The "content puller."
- Pulls content from GitHub, Reddit, YouTube, Instagram, TikTok.
- Indexes with semantic search via OpenAI embeddings.
- Stores in Postgres/pgvector on Supabase. Project ID: jfnkslhmcsiavhbueclf.
- Exposes content to Claude via an MCP server.
- STATUS: GitHub Actions deploy workflow was mid-debug. 409 empty repository error,
  likely from the INDEX_REPOS variable or a workflow edit not fully propagating.
- NOTE: KOS lives in a separate repo, not in Discord-Bots. This session is scoped
  to discord-bots only, so KOS code cannot be read from here.

## JARVIS (personal AI OS)

- Goal: make Claude Code function like a personal AI OS, Iron Man Jarvis style.
- Fully custom, voice-capable, agentic assistant with custom plugins, MCP connectors,
  automations, integrations.
- Python-based, targeting Windows/OneDrive. Files partially assembled, not fully delivered.
- Priority features: voice I/O, custom MCP servers, Discord integration, Roblox/game
  automation, content creation pipeline, fitness/training tracking, Clearcoat Co.
  business automation, unified dashboard.
- Build incrementally as Chris starts using Claude Code.

## Repos of interest

- git@github.com:she-llac/claude-counter.git
- git@github.com:drona23/claude-token-efficient.git
