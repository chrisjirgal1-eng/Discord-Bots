# Autonomous Potential: The Plan

Owner: Chris (Zenthra)
Date: 2026-06-27
Blueprint: ARIS (Auto-claude-code-research-in-sleep)
Status: ready to build

---

## 1. Executive summary

ARIS is not magic.
It is a folder of Markdown skills that run multi-step loops with one hard rule:
the model that writes the work never grades the work.

That rule is the whole game.
A long agent run can finish polished and be flat wrong.
The failure mode ARIS is built to catch: agents that rate their own output as a success when it is not. Self-assessed confidence runs far ahead of real pass rates.
The fix is cross-model review, hard gates, and budget caps.

My autonomous potential for you is real but bounded.
In an ephemeral cloud session I can run a full pipeline: search, build, test, commit, PR, merge.
I cannot stay alive overnight and I cannot keep a schedule firing past a container reset.
True scheduling needs an external host: GitHub Actions, Supabase, or Zapier. All free.

Six of your jobs can run with no human in the loop.
Four need a checkpoint. Outbound email to real coaches is always one of the four.
The first build is the KOS 409 deploy fix. It unblocks the highest-leverage job you have.

---

## 2. What my autonomous potential actually is

I can chain work, not just answer.
Workflow tool runs stages in order or in parallel.
Subagents run with their own model and effort.
154 VoltAgent specialists are committed and ready to call.

I can act on the outside world through 15 live MCP connectors.
GitHub, Supabase, Vercel, Gmail, Drive, Calendar, Notion, Slack, Stripe, Zapier, and more.
Credentials live in MCP config, not the container, so they survive a reset.

I can remember across sessions.
The memory bank is committed. graph.json is committed. The SessionStart hook is committed.
Anything I commit and push, the next session reads for near zero tokens.

What I cannot do in cloud:
Stay awake overnight. The session can die mid-run with no resume.
Keep a schedule firing without a live session. A scheduled job, even a durable one, only fires while a session REPL is running and idle. Once the web session ends, nothing runs the scheduler, so the job does not fire.
Run ARIS from its current location. The skills are extracted to /tmp this session and are not yet committed, so they reset.

The honest line:
I am a strong unattended worker inside one session.
For anything that must run on a clock without me, the clock has to live outside the container.

---

## 3. ARIS patterns worth stealing

Eight patterns. All proven in ARIS. All map to your stack.

1. Cross-model review.
The writer never judges itself.
20 Claude subagents give you 20 candidates, not 20 verdicts. Still one model.
The verdict goes to a different model family or a hard number.

2. Type-A vs Type-B gates.
Type-A is a fact: did the test pass, did 12 rows land. The agent can self-check these.
Type-B is a judgment: is this good, is this accurate. These route to a different judge.
A loop can drive. It cannot acquit.

3. Five-layer audit chain.
Not one review pass. A sequence, each asking a different question, each writing a verdict file.
A shell script reads all the files and refuses to ship if any is not green.

4. Fresh context per review.
The reviewer reads the raw files, never your summary.
If you pre-digest, the reviewer grades your framing, not the work.

5. Loop-until-dry with stall detection.
Every loop needs 4 exits: quality verdict, iteration cap, budget cap, no-progress.
2 stale rounds: force a structural change, not more tuning.
4 stale rounds: stop and ask a human.

6. Anti-repetition memory.
Failed attempts are stored so the next run skips them.
But never store "X tool is broken." That poisons every future session.
Store the fix, the config, the workaround. Never the failure as a fact.

7. Human checkpoint at irreversible steps.
Reversible and internal: run free.
Irreversible or outward-facing: stop and ask.
Drafting a wrong email is fixable. Sending it is not.

8. Budget caps as hard ceilings.
Token, time, and call count are separate from quality.
A loop that only exits on quality runs forever when quality never converges.

---

## 4. Capability inventory and honest limits

What survives a session reset: only committed and pushed files.
Lost every time: npm/pip installs, /tmp, shell state, anything uncommitted.

| Capability | Cloud (ephemeral) | Local / external host |
|---|---|---|
| Memory bank | Yes, committed | Yes |
| graphify graph | Yes, committed | Yes |
| SessionStart hook | Yes, commits survive | Yes |
| 15 MCP connectors | Yes, auth in config | Yes |
| Workflow pipeline mid-session | Yes | Yes |
| Subagents + 154 VoltAgents | Yes, configs committed | Yes |
| Commit / push / PR / merge | Yes | Yes |
| CronCreate / ScheduleWakeup firing on a clock | No, needs a live session; ends with the session | Yes |
| ARIS skills (current extraction) | No, uncommitted in /tmp; resets | Yes, once committed |
| Overnight unattended run | No, session can die | Yes |

The 9 real limits, named plainly:
1. No durable scheduling that fires on its own in cloud. A scheduled job only fires while a session is live and idle, and recurring jobs auto-expire after 7 days. Once the session ends, nothing runs the scheduler. For anything that must run on a clock without me, use GitHub Actions, Supabase, or Zapier.
2. No overnight runs in cloud. The browser dies, the run stops.
3. ARIS is extracted in /tmp and not yet committed, so it resets. Commit the skills to make it durable.
4. GitHub scope is one repo: discord-bots. KOS repo is out of reach this session.
5. graphify drifts after big refactors. Rebuild costs about $0.02.
6. The 154 VoltAgents are unaudited. A Haiku validation pass costs about $0.10.
7. Twitter/X and TikTok posting are platform-blocked. No MCP or Zapier workaround.
8. Discord is Zapier-mediated. No native real-time listening without a Zap.
9. Memory bank is only as current as the last commit. End every session with an update.

Cost map for routing, per million tokens (input / output):
Haiku $1 / $5, Sonnet $3 / $15, Opus $5 / $25, Fable $10 / $50.
Agentic loops are output-heavy, so weight the output column when you route.
Push search and bulk edits to Haiku. Keep judgment on Opus. Reserve Fable for the bug Opus keeps missing.

---

## 5. Prioritized roadmap

Three phases. Each item: front, value, where it runs, autonomy.

### NOW (this week)

A. Fix the KOS 409 deploy. (#7)
Front: KOS. Value: high. Runs: needs KOS repo in scope. Autonomy: semi, flag before final push.
Why first: it unblocks everything downstream. KOS is not a product until the deploy is green.
First build: open a session scoped to the KOS repo, read the failing Actions workflow, isolate the INDEX_REPOS variable, patch, push.

B. Commit ARIS skills you actually want. (infra)
Front: all. Value: high. Runs: cloud. Autonomy: full.
Why: ARIS resets every session today because it lives in /tmp uncommitted. Commit the subset and pull it in the SessionStart hook to make it permanent.
First build: copy idea-discovery, kill-argument, auto-review-loop, citation-audit, and the shared-references into a committed skills/ dir.

C. Audit the 154 VoltAgents. (infra)
Front: all. Value: medium. Runs: cloud. Autonomy: full.
First build: one Haiku subagent pass validating each config against the current tool list. About $0.10. Flag broken ones.

### NEXT (this month)

D. KOS nightly indexing job. (#1)
Front: KOS. Value: highest once deploy is green. Runs: GitHub Actions cron or $5/mo Fly.io. Autonomy: full.
Pass gate is a Supabase row count. A hard number, no judgment. Posts status to Discord.
First build: a GitHub Actions cron workflow that runs the existing TypeScript pull, embeds, upserts to pgvector, writes a row count, pings Discord via Zapier.

E. Guild churn alert. (#2)
Front: Zenthra. Value: high at 1,300 members. Runs: Actions cron. Autonomy: full.
Threshold is numeric: 0 messages in 14 days. Posts a ranked list to a staff channel.

F. Weekly progress digest. (#8)
Front: all. Value: medium. Runs: cloud, weekly. Autonomy: full.
Reads progress-log, KOS row counts, Calendly bookings, guild activity. Writes 10 lines to active-context.md and commits.
Pure read plus commit. No outbound. Keeps the memory bank current with no manual effort.

G. Bot code-review loop. (#5)
Front: Zenthra. Value: medium. Runs: cloud on push. Autonomy: full, read-only.
A Sonnet subagent reviews each diff for queue and voice-lock bugs, posts inline comments, never merges.
The /code-review skill already exists. Wire it to a push trigger.

### LATER (next quarter)

H. Content-idea pipeline. (#3)
Front: TikTok/YouTube. Value: high. Runs: cloud weekly. Autonomy: semi, you pick the angle.
Searches trending Roblox terms, runs idea-vs-weak-point critique, writes 5 ranked angles to Notion.

I. Clearcoat booking confirmation. (#6)
Front: Clearcoat. Value: medium. Runs: cloud on Zapier webhook. Autonomy: full.
New Calendly booking fires a webhook. I draft a confirmation plus prep, send via Gmail.

J. Coach outreach drafting. (#4)
Front: D1 track. Value: high. Runs: cloud on demand. Autonomy: human checkpoint, firm.
Pulls coach and school from a Notion row, writes 3 versions in your real voice, drops a Gmail draft. You send. Never autonomous outbound to a real person.

K. Roblox trend scan + JARVIS scaffold. (#9, #10)
Trend scan: daily search, 5 bullets to a guild news channel, full autonomy.
JARVIS: cloud for design, persistent Windows machine for runtime. Human sign-off on architecture.

---

## 6. The 3 likeliest failure points

1. Self-grading loops.
The trap: I run a "keep improving until good" loop, decide I like my own output, and stop.
100 rounds of Claude judging Claude is still one model.
Avoid it: every quality gate routes to a different model family or a hard number. KOS pass gate is a row count, not my opinion.

2. Poisoned memory.
The trap: a transient error like a 409 or a 429 gets written into active-context.md as a durable fact.
Next session loads it, believes "KOS is broken," and cites it against the work after the real cause is fixed.
Avoid it: never store a failure as a fact. Store the fix, the config, the workaround. Screen writes to the memory bank.

3. The schedule that quietly never runs.
The trap: I set a scheduled job in a cloud session, it works while the session is live, the session ends, and the job stops firing with nobody noticing for a week.
Avoid it: no recurring job depends on a live session. All recurring jobs run on GitHub Actions, Supabase, or Zapier. Each writes a heartbeat so a missed run is visible.

---

## 7. One thing to do first

Fix the KOS 409 deploy.
It is narrow, bounded, and has a clear pass condition: Actions go green.
It unblocks the nightly indexing job, which is the single highest-leverage automation you have.
The KOS repo is out of scope in this session, so the next session that can reach it should start there and do nothing else until it is green.
