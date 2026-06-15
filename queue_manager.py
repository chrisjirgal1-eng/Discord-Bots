from collections import deque
from typing import Optional
from audio import Track


class GuildQueue:
    def __init__(self):
        self._queue: deque[Track] = deque()
        self.current: Optional[Track] = None
        self.volume: float = 0.5
        self.loop_track: bool = False

    def add(self, track: Track):
        self._queue.append(track)

    def add_many(self, tracks: list[Track]):
        self._queue.extend(tracks)

    def next(self) -> Optional[Track]:
        if self.loop_track and self.current:
            return self.current
        if self._queue:
            self.current = self._queue.popleft()
            return self.current
        self.current = None
        return None

    def clear(self):
        self._queue.clear()
        self.current = None

    def peek(self, n: int = 10) -> list[Track]:
        return list(self._queue)[:n]

    def __len__(self) -> int:
        return len(self._queue)


class QueueManager:
    def __init__(self):
        self._guilds: dict[int, GuildQueue] = {}

    def get(self, guild_id: int) -> GuildQueue:
        if guild_id not in self._guilds:
            self._guilds[guild_id] = GuildQueue()
        return self._guilds[guild_id]

    def remove(self, guild_id: int):
        self._guilds.pop(guild_id, None)
