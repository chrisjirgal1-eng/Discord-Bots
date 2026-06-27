# Discord music bot: code review

Date: 2026-06-27. Reviewer: Opus subagent in fresh context, confirmed against source.
Files: bot.py, audio.py, queue_manager.py.

queue_manager.py is essentially correct. The real defects cluster around one root cause:
the per-guild asyncio lock exists but the playback path does not use it.

## Fixed this pass (safe, isolated, no concurrency change)

- get_running_loop. audio.py used `asyncio.get_event_loop()` (deprecated). Now
  `asyncio.get_running_loop()`. Zero behavior change.
- Empty stream guard. A single non-playlist result with no `url` built a Track with
  `stream_url=''`, which made `FFmpegPCMAudio('')` fail in the playback thread and stall
  silently. Now raises a clear `ValueError` instead. The playlist path already guarded this.

## Applied 2026-06-27 (Chris said "add everything")

All five below are now in bot.py. A fresh Opus reviewer checked the diff: no deadlock
(the lock is never acquired re-entrantly), auto-disconnect has no false triggers, the
play_next guard does not block normal advance, guild_only is safe with copy_global_to.
Still recommended: a dev-guild smoke test before relying on them in production, since the
review verified logic, not a live run.

1. Per-guild lock now wraps `_auto_join`, and `play_next` early-returns if `vc.is_playing()`.
2. Auto-disconnect when the last human leaves the bot's channel (clears the queue first).
3. `@app_commands.guild_only()` on all 9 commands (no more DM crash).
4. Reconnect `discard(gid)` moved into a `finally`.
5. `_auto_join` guard runs under the lock for the on_ready and reconnect paths.

### Original findings (for reference)

Ranked by value.

1. Use the per-guild lock (root cause). HIGH.
   `play_next` / `_advance` never acquire `self._lock(guild_id)`, but `/play`, `_auto_join`,
   and the `after_cb` advance can all call `play_next` for the same guild at once. Result:
   `vc.play()` on a client that just started, or a freshly popped track dropped.
   Fix: guard the play/advance start path with the lock and re-check
   `vc.is_playing()/is_paused()` inside the guarded section. Root cause of items 1, 2, 4, 5.

2. Auto-disconnect on empty channel. MED, resource leak.
   `on_voice_state_update` auto-joins when humans appear but never disconnects when the last
   human leaves. The bot holds the voice client and any ffmpeg process forever, across guilds.
   Fix: when the bot's channel has no non-bot members, `await vc.disconnect()` and clear the queue.

3. DM crash. MED.
   Commands use `interaction.guild` directly and the tree syncs globally with no
   `guild_only`. In a DM, `interaction.guild` is None and `.voice_client` raises, giving the
   user "interaction failed".
   Fix: add `@app_commands.guild_only()` to the commands (or guard `interaction.guild is None`).

4. Reconnect dedupe gap. MED.
   In `on_voice_state_update`, `self._reconnecting.discard(gid)` runs before `_auto_join`
   awaits `connect()`, so a second disconnect during that await starts a duplicate reconnect.
   Also `_auto_join` rejoins the most populated channel, not the one the bot was kicked from.
   Fix: move the discard into a `finally` after `_auto_join` completes.

5. Unlocked `_auto_join` on the on_ready and reconnect paths. MED.
   The member-join path locks and re-checks `voice_client is None`, but `on_ready` and
   reconnect call `_auto_join` unlocked, so two concurrent calls can both pass the guard and
   both call `connect()` ("already connected" error / duplicate client).
   Fix: move the lock + recheck inside `_auto_join` and route all callers through it.

## Low priority

- `loop_track` defaults False with no command to toggle it. Dead config until a loop command
  is added. If toggled, `next()` would never drain the queue.

## How to proceed

Items 1 and 5 share the lock fix, so do them together. Items 2 and 3 are independent and
safe-ish. None can be runtime-verified without a live bot and a voice channel, so each should
be applied, then smoke-tested in a dev guild before shipping. Say the word and I will apply
them on a branch for your review.
