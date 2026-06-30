# TECHNIQUES

Digest of the saved videos (130 transcribed across two batches), judged against the 3 goal videos. Honest and ranked.
Each training technique earns a place only if it moves the setup toward what the goals describe.
Source = Instagram shortcode (see tools/video-urls.txt). Status = new / already-have / hype-or-off-target.

## The goal (north star), in 5 lines

From the 3 goal videos (DZlQ7GZnJR7, DZu4FFeDtIH, DZVEN4gMRXV):

1. JARVIS is a Claude (Fable 5) **agentic personal OS**, one command center Chris owns, not rented.
2. It has **persistent memory**: a knowledge graph (Graphify + Obsidian) so Claude stops forgetting when the tab closes.
3. It runs **always-on autonomous loops** (hosted, 24/7) that act, verify, and report, with a hard budget exit.
4. It is **voice-capable** ("Wide awake, sir"): it briefs Chris on real numbers and asks what to handle first.
5. It **synthesizes to the next move**, it does not just draw pretty dashboards. It says "do X, here are the follow-on effects."

The training videos are the means. JARVIS is the end.

---

# Round 2 - 69 new videos (2026-06-30)

65 of 69 transcribed (4 had no audio: 3 image carousels + 1 silent reel). Judged against the same
goal. Most of the batch repeats Round 1 themes (graph memory, multi-agent swarms, skill lists),
which confirms the direction but earns no new change. A few items are genuinely new.

## NEW, high-value (apply these)

| Technique | Source | Value | Status | Action |
|---|---|---|---|---|
| Plan with the premium model, build with the cheaper one. Fable 5 is the most expensive and over-explains, so spend it only on low-volume planning and architecture, then hand a tight plan to Opus for the bulk build. A vague plan makes the cheaper model rethink everything, so the plan has to be tight. | DZc-ajJKT1L | high | new (routing refinement) | Add to model-routing.md: premium model for planning (low token volume), cheaper frontier for the build. Pairs with prompt-first-planning. |
| Ultracode / Dynamic Workflows (Opus 4.8): `/effort` -> Ultra spawns 100+ parallel sub-agents in one session for hard tasks, then returns one checked result. Token-heavy: one creator reported 72 agents at once and a 250-instance workflow. | DY5yKZ8Jgke, DZT9OtvJj4B, DY7-4V7htXM, DZs4Caci87V | high | new (capability) | Note in throughput.md: reach for Ultra / dynamic workflows on hard parallel work only, always under the verification.md budget cap. This is the native version of the swarm tools the reels keep pushing. |
| MCP tunnels + self-hosted sandboxes: run Claude agents on your own infra (your box or VPC), same model and skills, nothing leaving the machine. Removes the "data leaves the building" objection for regulated buyers. | DYxSlEjOMq3 | med | new (hosting option) | Folds into the "owned, not rented" goal and the autonomous-loop hosting decision. An option, not an immediate change. |
| Clone an open-source repo into the project, then Graphify the clone, so the agent reads the real code (not just the README) with a semantic map first. | DaLg2dBjQah | med | new (extends graphify) | Optional small skill. Natural extension of the graphify the setup already runs. |

## Confirms the goal / already-have (no rebuild)

| Theme | Sources (sample) | Note |
|---|---|---|
| Graphify + Obsidian "second brain", 70x fewer tokens, Karpathy raw-folder origin. | DXxTmplOABg, DYzrTT7u5TN, DZQcHlwBO44, DZyCJeHEVqK, DWo1P-KDpMf, DYYjiiEJh5m, DZMFrWqszBt | Goal step 1, already core. The most repeated theme in the batch. |
| Multi-agent swarms with shared memory + an orchestrator (Claude Flow, RooFlow-likes, "harness" framing). | DZmqlETDkLl, DZSU_0WMfqf, DY5yJSAxP00, DXe8RlbCSrv, DZg2-lVqvFg | The 154 subagents + model-routing already cover this. "Harness" just names what is built. |
| Agentic OS, not a pretty dashboard: 24/7 daemon, phone control, self-improving agents. | DYAL7pNk-1F, DWINJhFDW-v, DXkSk6ZjgmD, DYtVwjzsTZC | This is the JARVIS goal restated. Confirms direction. |
| Skill ecosystems and skill-creator tools (Superpowers, GSD, Context Mode, ClaudeMem, stop-slop, grill-me, slash review). | DXGQ6-2t11w, DXGRONttjhp, DZfULkBD_aB, DZY9plMOHNa | SkillSmith + the local skills + /code-review + handoff + memory-bank already cover these. stop-slop = the banned-words rule. |
| App security for vibe-coded apps: turn on RLS, no client-side admin checks, rate-limit auth, no tokens in localStorage, minify, free security-review plugin. | DXvKgfFJF7a, DZK-53TAAW2, DZK9n6mxjFT, DZsXW-HonCi, DYqJY7TgN-d, DZOS1ywhWSl | The `/security-review` skill already exists; run it on bot.py and the websites. Worth a short app-security checklist if those ship to users. |
| Billing split (June 15): automated, headless, Hermes, OpenClaw agents bill at full API rate. | DZkFtPxigOy | Already logged in Round 1 (DZltJGZsGnG) and the cost map. |

## HYPE or off-target (skipped, logged honestly)

- LLM "all vulnerabilities / jailbreak" repo (DaI2IMrphj6) and "Fable 5 banned, paste this prompt" echoes: sketchy, skip.
- n8n Chat (DT8PqVCEVEi): off-target tool, not Claude.
- Trading (DaFZTFPgF0V), "Project Quant" satire (DZtlkLmuyFv), Meta brain-to-text news (DaLt5fWvVEM), 3D-print iteration (DXgDNe0DV89): off-target.
- Arc-reactor / JARVIS roleplay shorts (DY26vG0h0G-, DZOHIqmSAcj, DZLivf_h_Vm) and ~16 music or filler clips: no technique. Expected for social reels.

## What to apply from Round 2

Small and earned only:
1. model-routing.md: plan with the premium model, build with the cheaper one (DZc-ajJKT1L).
2. throughput.md: a note on Ultra / dynamic workflows for hard parallel work, under the budget cap.

Everything else confirms the existing direction or did not earn a change. Quality over volume.

---

# Round 1 (original 65 videos)

## NEW, high-value (apply these)

| Technique | Source | Value | Status | Action |
|---|---|---|---|---|
| Session handoff ritual: before ending, write `handoff.md` (goal, state, files, what failed, next), then `/clear` and a fresh session reads it. Beats compaction, which carries bad assumptions forward. | DYNWWdiMiH7 | high | new | Add a `handoff` skill. The repo has active-context.md but no clean end-of-session continuation doc. |
| Synthesis over visualization: the dashboard must recommend the next action and its follow-on effects, not just map how things connect. "Chess, not checkers." | DZY7s0LK2vj + goal reel | high | new (principle) | Bake into the JARVIS entry point: it routes AND recommends, never just displays. |
| Voice-first build recipe: write a PRD first, give it calendar/email/Stripe access and a local UI, voice via 11 Labs (TTS) + Deepgram (STT), grab the voice ID. | DXKeid0jyqG, DZ7kMxgMboD | high | new | Capture as the JARVIS voice + entry-point spec (Phase 4). Wire to existing MCP connectors. |
| Content pipeline as named specialist agents + one chat to run them: scout, hook analyst, voice analyst, topic finder, script drafter, with an orchestrator. | DZ_xzicxQPx + goal reel | high | new (model) | Model the JARVIS content pipeline this way; reuse the existing caption/zen-announce skills as the workers. |
| Cron-driven loop that runs skills on a schedule, self-verifies, reports to Slack, with a budget stop. | DZ8JVSpGOtK | med | new (scheduling) | Maps to the durable-scheduling plan (GitHub Actions / Zapier). One checker + budget cap already required by verification.md. |

## ALREADY-HAVE (confirm, do not rebuild)

| Technique | Source | Status | Note |
|---|---|---|---|
| Graphify knowledge graph in Obsidian, persistent, ~70x fewer tokens per search. | DW4Gc3PDibh, DYpsvyDu2by, DZT5cH-RLsV | already-have | graphify installed; graph.json committed. This is goal Step 1, already done. |
| Loops need a separate verifier and a budget cap; the writer never grades itself. "I write loops, not prompts." | DZ8JVSpGOtK, DZXsQkKgEeQ, DYPld5xRb8u | already-have | This is verification.md verbatim. The head of Claude Code confirms the thesis. |
| Import a big library of specialist subagents with one command. | DZDUd0kS7lw, DZB60nMxwJa | already-have | 154 VoltAgents already registered. |
| Route cheap/parallel: basic tasks to cheaper models, hard tasks to the frontier, shared memory. | DWtsJ4XAgw_ | already-have | model-routing.md covers this. |
| Keep secrets in a gitignored env file, set hard billing caps, restrict the blast radius. | DXmVjvwjpgQ, DVe_2itjw5a | already-have | .env is gitignored; Groq key stored there this session. |
| Make Claude design like a senior engineer first (architecture, audit, security) before writing code. | DZzzH4Cje60 | already-have | coding-discipline.md "think before coding." |
| Build skills, not agents; a skill is folders + one SKILL.md. SkillSmith scaffolds them. | DZirH1hNQ8c, DZkyFMrkcLZ | already-have | 6 skills exist in a consistent format. Anthropic's own guidance. |
| Avoid AI tells (no em dashes, humanized output). | DYtJmUQtL4r ("ghost") | already-have | Already a kickoff rule and scanned before each commit. |

## Worth noting, optional (not applied now)

| Technique | Source | Value | Why not now |
|---|---|---|---|
| Design skills for real polish: motion/easing, spacing/typography, real design references. | DYU6TXpDxtt | med | Useful for the dashboard and Clearcoat site visuals in Phase 4, not a standalone change. |
| App-quality checklist: button labels, optimistic UI, pagination, fix N+1, async ops. | DaBJZy8ovVY | med | Maps to /code-review. The Devin merge already raised bot quality this session. |
| Video-generation pipelines (Remotion/Manim, Higgsfield via Playwright MCP). | DYf-n9PguD5, DW7WShljcWg | med | Content-pipeline adjacent but tool-specific; revisit if Chris wants faceless video at scale. |
| Billing change: automated agents bill at full API rate on a separate line. | DZltJGZsGnG | med | Cost context for 24/7 loops; already reflected in the autonomous-potential cost map. |

## HYPE or off-target (skipped, logged honestly)

- "Secret Claude codes" (God Mode, L99, OODA, ghost). DYtJmUQtL4r. Prompt tricks, mostly hype; the one real bit (avoid AI tells) is already a rule.
- "Fable 5 banned, paste this system prompt to get it back." DZqViOYxmru. Sketchy jailbreak claim, skip.
- "Jarvis released free, booked my dinner autonomously." DXpsxCtD-tU. An ad. The capability vision is already the goal.
- Trading content: liquidity sweeps, backtesting, Monte Carlo, AI trading layers, TradingView MCP. DXEy4gWDhib, DZc6e5MByuj, DZsAke9RXxu, DZG6aKYNnpr, DaBWMuYtZRq, DXFc6EjDdgy, DZbzF7VgXwT. Off-target: trading is not one of Chris's projects (Zenthra, Clearcoat, KOS, JARVIS, D1 track).
- Trademark an idea (DV1muB2EXvd), Roblox dev mindset (DZAm8rtKkBW), "watch these 3 YouTube videos" (DZDkJUgIBtf). Useful life/biz advice, not a JARVIS technique.
- Systemize and delegate so the business runs without you (DXCxXufElFW). Good mindset, already the spirit of the autonomous plan.
- ~21 reels were music, lyrics, or filler audio (Outro Music, "Bye", song clips). No technique. Expected for social reels.

## What gets applied in Phase 3

Only the new, high-value, simple items:
1. A `handoff` skill (the one clean gap a video exposed).
2. The synthesis-to-next-action principle and the voice/content-pipeline models feed Phase 4 (build toward JARVIS), not separate artifacts.

Everything else is already in the setup or did not earn a change. Quality over volume.
