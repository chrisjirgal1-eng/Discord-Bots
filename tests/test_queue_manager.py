import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import Track
from queue_manager import GuildQueue, QueueManager


def _make_track(title="Test Track", url="http://stream.url"):
    return Track({"title": title, "url": url, "webpage_url": f"http://page/{title}"})


class TestGuildQueue:
    def test_initial_state(self):
        q = GuildQueue()
        assert q.current is None
        assert q.volume == 0.5
        assert q.loop_track is False
        assert len(q) == 0

    def test_add_single_track(self):
        q = GuildQueue()
        t = _make_track("Song A")
        q.add(t)
        assert len(q) == 1

    def test_add_many_tracks(self):
        q = GuildQueue()
        tracks = [_make_track(f"Song {i}") for i in range(5)]
        q.add_many(tracks)
        assert len(q) == 5

    def test_next_returns_tracks_in_order(self):
        q = GuildQueue()
        tracks = [_make_track(f"Song {i}") for i in range(3)]
        q.add_many(tracks)

        first = q.next()
        assert first.title == "Song 0"
        assert q.current is first
        assert len(q) == 2

        second = q.next()
        assert second.title == "Song 1"
        assert q.current is second
        assert len(q) == 1

    def test_next_returns_none_when_empty(self):
        q = GuildQueue()
        result = q.next()
        assert result is None
        assert q.current is None

    def test_next_clears_current_when_exhausted(self):
        q = GuildQueue()
        q.add(_make_track("Only"))
        q.next()  # pops "Only"
        result = q.next()  # nothing left
        assert result is None
        assert q.current is None

    def test_loop_track_repeats_current(self):
        q = GuildQueue()
        q.add(_make_track("Loop Me"))
        q.add(_make_track("Never Reached"))
        q.loop_track = True

        first = q.next()
        assert first.title == "Loop Me"

        # With loop enabled, next() returns current again
        second = q.next()
        assert second.title == "Loop Me"
        assert len(q) == 1  # queue not consumed

    def test_loop_track_does_nothing_without_current(self):
        q = GuildQueue()
        q.loop_track = True
        result = q.next()
        assert result is None

    def test_clear_resets_queue(self):
        q = GuildQueue()
        q.add_many([_make_track(f"Song {i}") for i in range(5)])
        q.next()  # set current
        assert q.current is not None
        assert len(q) == 4

        q.clear()
        assert q.current is None
        assert len(q) == 0

    def test_peek_returns_subset(self):
        q = GuildQueue()
        tracks = [_make_track(f"Song {i}") for i in range(15)]
        q.add_many(tracks)

        peeked = q.peek()
        assert len(peeked) == 10  # default n=10
        assert peeked[0].title == "Song 0"
        assert peeked[9].title == "Song 9"

    def test_peek_custom_n(self):
        q = GuildQueue()
        tracks = [_make_track(f"Song {i}") for i in range(5)]
        q.add_many(tracks)

        peeked = q.peek(n=3)
        assert len(peeked) == 3

    def test_peek_does_not_consume_queue(self):
        q = GuildQueue()
        q.add_many([_make_track(f"Song {i}") for i in range(5)])
        q.peek()
        assert len(q) == 5

    def test_volume_can_be_changed(self):
        q = GuildQueue()
        q.volume = 0.8
        assert q.volume == 0.8

    def test_len_reflects_queue_not_current(self):
        q = GuildQueue()
        q.add_many([_make_track(f"Song {i}") for i in range(3)])
        q.next()  # moves one to current
        assert len(q) == 2


class TestQueueManager:
    def test_get_creates_new_guild_queue(self):
        qm = QueueManager()
        q = qm.get(12345)
        assert isinstance(q, GuildQueue)
        assert len(q) == 0

    def test_get_returns_same_queue_for_same_guild(self):
        qm = QueueManager()
        q1 = qm.get(12345)
        q1.add(_make_track("Persistent"))
        q2 = qm.get(12345)
        assert q1 is q2
        assert len(q2) == 1

    def test_get_returns_different_queues_for_different_guilds(self):
        qm = QueueManager()
        q1 = qm.get(111)
        q2 = qm.get(222)
        assert q1 is not q2

    def test_remove_deletes_guild_queue(self):
        qm = QueueManager()
        q = qm.get(12345)
        q.add(_make_track("Song"))
        qm.remove(12345)
        # Getting again should return fresh empty queue
        q_new = qm.get(12345)
        assert len(q_new) == 0

    def test_remove_nonexistent_guild_is_noop(self):
        qm = QueueManager()
        qm.remove(99999)  # should not raise
