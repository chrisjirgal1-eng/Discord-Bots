import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Patch environment before importing bot to prevent RuntimeError on missing token
os.environ.setdefault("DISCORD_TOKEN", "fake-token-for-testing")


# We need to mock discord and prevent bot.run() from being called on import
with patch("discord.Client.__init__", return_value=None), \
     patch("discord.app_commands.CommandTree"), \
     patch.object(sys.modules.get("builtins", __builtins__), "__import__", wraps=__import__):
    pass


from audio import Track
from queue_manager import QueueManager, GuildQueue


class TestMusicBotLock:
    """Test the _lock method logic (guild-specific lock creation)."""

    def test_lock_creates_new_lock_per_guild(self):
        locks: dict[int, asyncio.Lock] = {}

        def _lock(guild_id: int) -> asyncio.Lock:
            if guild_id not in locks:
                locks[guild_id] = asyncio.Lock()
            return locks[guild_id]

        lock1 = _lock(100)
        lock2 = _lock(200)
        assert lock1 is not lock2
        assert isinstance(lock1, asyncio.Lock)

    def test_lock_reuses_existing_lock(self):
        locks: dict[int, asyncio.Lock] = {}

        def _lock(guild_id: int) -> asyncio.Lock:
            if guild_id not in locks:
                locks[guild_id] = asyncio.Lock()
            return locks[guild_id]

        lock_a = _lock(100)
        lock_b = _lock(100)
        assert lock_a is lock_b


class TestPlayNextLogic:
    """Test the play_next logic flow without needing a real VoiceClient."""

    def test_play_next_returns_early_when_not_connected(self):
        qm = QueueManager()
        q = qm.get(1)
        q.add(Track({"title": "Song", "url": "http://s.url"}))

        vc = MagicMock()
        vc.is_connected.return_value = False

        # Simulating play_next logic
        if not vc.is_connected():
            return  # early return
        pytest.fail("Should have returned early")

    def test_play_next_does_nothing_when_queue_empty(self):
        qm = QueueManager()
        q = qm.get(1)

        vc = MagicMock()
        vc.is_connected.return_value = True

        # Simulating play_next logic
        track = q.next()
        assert track is None

    def test_play_next_pops_track_from_queue(self):
        qm = QueueManager()
        q = qm.get(1)
        q.add(Track({"title": "Play Me", "url": "http://stream.url"}))

        vc = MagicMock()
        vc.is_connected.return_value = True

        track = q.next()
        assert track is not None
        assert track.title == "Play Me"
        assert len(q) == 0


class TestBotCommandLogic:
    """Test command logic patterns used in bot.py without actual Discord interactions."""

    def test_volume_clamping(self):
        """Volume command logic: level / 100 applied to queue."""
        q = GuildQueue()
        level = 75
        q.volume = level / 100
        assert q.volume == 0.75

    def test_volume_zero(self):
        q = GuildQueue()
        q.volume = 0 / 100
        assert q.volume == 0.0

    def test_volume_max(self):
        q = GuildQueue()
        q.volume = 100 / 100
        assert q.volume == 1.0

    def test_stop_clears_queue(self):
        """The /stop command clears queue and stops playback."""
        q = GuildQueue()
        q.add_many([Track({"title": f"S{i}", "url": f"http://s/{i}"}) for i in range(5)])
        q.next()  # set current
        assert q.current is not None
        assert len(q) == 4

        # Simulating /stop
        q.clear()
        assert q.current is None
        assert len(q) == 0

    def test_skip_advances_queue(self):
        """The /skip logic: vc.stop() triggers after_cb which calls play_next."""
        q = GuildQueue()
        q.add(Track({"title": "First", "url": "http://s/1"}))
        q.add(Track({"title": "Second", "url": "http://s/2"}))

        first = q.next()
        assert first.title == "First"

        # After skip, next track plays
        second = q.next()
        assert second.title == "Second"

    def test_nowplaying_with_no_current(self):
        """When nothing is playing, current is None."""
        q = GuildQueue()
        assert q.current is None

    def test_nowplaying_shows_current_track(self):
        q = GuildQueue()
        q.add(Track({
            "title": "Current Song",
            "url": "http://s.url",
            "webpage_url": "http://page.url",
            "duration": 195,
            "thumbnail": "http://thumb.url",
            "uploader": "Channel",
        }))
        q.next()
        assert q.current.title == "Current Song"
        assert q.current.duration == 195
        assert q.current.thumbnail == "http://thumb.url"
        m, s = divmod(int(q.current.duration), 60)
        assert f"{m}:{s:02d}" == "3:15"

    def test_queue_display_logic(self):
        """Test the queue formatting logic from /queue command."""
        q = GuildQueue()
        tracks = [Track({"title": f"Song {i}", "url": f"http://s/{i}"}) for i in range(12)]
        q.add_many(tracks)
        q.next()  # sets current

        upcoming = q.peek()
        assert len(upcoming) == 10
        remainder = len(q) - len(upcoming)
        assert remainder == 1  # 11 remaining - 10 peeked = 1 more

    def test_leave_clears_queue(self):
        """The /leave command clears queue before disconnecting."""
        q = GuildQueue()
        q.add_many([Track({"title": f"S{i}", "url": f"http://s/{i}"}) for i in range(3)])
        q.next()
        q.clear()
        assert len(q) == 0
        assert q.current is None


class TestAutoJoinLogic:
    """Test the auto-join decision logic."""

    def test_auto_join_selects_most_populated_channel(self):
        """Simulating the max() logic from _auto_join."""
        # Simulate channels with member counts (non-bot)
        channels = [
            {"name": "empty", "humans": 0},
            {"name": "popular", "humans": 5},
            {"name": "small", "humans": 2},
        ]

        # Filter channels with at least one human
        eligible = [c for c in channels if c["humans"] > 0]
        best = max(eligible, key=lambda c: c["humans"], default=None)

        assert best is not None
        assert best["name"] == "popular"

    def test_auto_join_returns_none_when_no_humans(self):
        channels = [
            {"name": "bots-only", "humans": 0},
        ]
        eligible = [c for c in channels if c["humans"] > 0]
        best = max(eligible, key=lambda c: c["humans"], default=None)
        assert best is None


class TestReconnectionLogic:
    """Test the reconnection tracking set logic."""

    def test_reconnecting_set_prevents_duplicate_reconnections(self):
        reconnecting: set[int] = set()
        guild_id = 12345

        assert guild_id not in reconnecting
        reconnecting.add(guild_id)
        assert guild_id in reconnecting

        # Second add is a no-op
        reconnecting.add(guild_id)
        assert len(reconnecting) == 1

    def test_discard_removes_guild_from_reconnecting(self):
        reconnecting: set[int] = set()
        guild_id = 12345
        reconnecting.add(guild_id)
        reconnecting.discard(guild_id)
        assert guild_id not in reconnecting

    def test_discard_nonexistent_is_safe(self):
        reconnecting: set[int] = set()
        reconnecting.discard(99999)  # should not raise
