# Take this setup anywhere

This makes everything built here (rules, skills, memory bank) available to your other
projects and to plain Claude Code, not just the discord-bots repo.

## Two ways to install

### 1. Global (your computer, all projects)

Best for "normal Claude has everything I have." Installs to `~/.claude`, which every
Claude Code session on that machine reads, regardless of project.

```sh
tools/install-claude-setup.sh global
```

What it does:
- Copies `.claude/rules/` (model-routing, verification, learning) to `~/.claude/rules/`.
- Copies `.claude/skills/` (coach-email, caption, zen-announce, clearcoat-post) to `~/.claude/skills/`.
- Copies the memory bank to `~/.claude/memory-bank/`.
- Appends a managed block to `~/.claude/CLAUDE.md` that loads the must-have memory every session.
- Idempotent. Re-run anytime. Does not delete anything you made.

Then install the per-session tools once:

```sh
uv tool install graphifyy && graphify install --platform claude
```

### 2. Per-repo (another project, including cloud sessions)

Best when a specific repo needs the setup committed so it survives ephemeral cloud sessions.

```sh
tools/install-claude-setup.sh repo /path/to/other-repo
```

What it does:
- Copies rules, skills, memory bank, and the SessionStart hook into that repo.
- Commit `.claude/` and `memory-bank/` there so they persist.
- Register the hook in that repo's `.claude/settings.json` (copy the block from this repo).

## The honest caveat

- On a persistent machine, global install is permanent.
- In ephemeral cloud sessions, `~/.claude` resets, so for a cloud project use the per-repo
  install and commit the files. The SessionStart hook then rebuilds graphify and the
  VoltAgent subagents each session.

## What is portable vs not

| Piece | Portable how |
|---|---|
| Rules (routing, verification, learning) | Copied to ~/.claude/rules or the repo |
| Skills (coach-email, caption, ...) | Copied to ~/.claude/skills or the repo |
| Memory bank (who you are, projects, lessons) | Copied to ~/.claude/memory-bank or the repo |
| graphify, VoltAgent subagents | Reinstalled per session via the hook or the one-liners above |
| MCP connectors (GitHub, Supabase, ...) | Already global; auth lives in MCP config, not a repo |

## Process videos in bulk (the fix for the Instagram wall)

The cloud session cannot download Instagram (its proxy returns 403) and has no transcription
key. The fix: run the heavy part on your own computer, then commit the text output, which
Claude reads in any session.

1. Get a free Groq API key at https://groq.com (free tier, fast Whisper).
2. Put your links in `tools/video-urls.txt`, one per line.
3. Run, on your machine:

```sh
export GROQ_API_KEY=gsk_your_key
tools/watch-batch.sh tools/video-urls.txt transcripts/
```

It downloads each video's audio with yt-dlp and transcribes it with Groq Whisper, writing
one `.txt` per video. Failures are marked and skipped, so a blocked or removed video does
not stop the batch.

4. Commit the transcripts:

```sh
git add transcripts/ && git commit -m "Add video transcripts" && git push
```

5. Tell Claude to read `transcripts/` and apply the lessons. Text works everywhere, no proxy,
   no key needed on the cloud side.

Needs yt-dlp and ffmpeg locally. The global installer note above covers both.
