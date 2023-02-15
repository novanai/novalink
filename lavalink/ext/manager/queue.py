from __future__ import annotations

import random
import typing

import lavalink.client as client
import lavalink.events as events
import lavalink.models as models

if typing.TYPE_CHECKING:
    import lavalink.ext.manager as manager


class Queue:
    def __init__(
        self,
        guild_id: int,
        lavalink: client.Lavalink,
        player_manager: manager.PlayerManager,
    ) -> None:
        self.guild_id = guild_id
        self.lavalink = lavalink
        self.player_manager = player_manager

        self.queue: list[models.Track] = []
        self.now_playing_pos: int = 0
        self.is_paused: bool = False

        for event in (
            events.TrackEndEvent,
            events.TrackStuckEvent,
            events.TrackExceptionEvent,
        ):
            lavalink.listen(event, self.track_events)

    def __len__(self) -> int:
        return len(self.queue)

    @property
    def now_playing(self) -> models.Track | None:
        if self.now_playing_pos < len(self.queue):
            return self.queue[self.now_playing_pos]

    async def track_events(
        self,
        event: events.TrackEndEvent
        | events.TrackStuckEvent
        | events.TrackExceptionEvent,
    ) -> None:
        print(
            f"Event: {event.__class__.__name__}. Position: {self.now_playing_pos}. Queue length: {len(self.queue)}"
        )

        if event.guild_id != self.guild_id or self.is_paused:
            return

        if (
            isinstance(event, events.TrackEndEvent)
            and event.reason is not models.TrackEndReason.FINISHED
        ):
            return

        await self.next()

    async def add(self, track: models.Track) -> None:
        self.queue.append(track)

        if not self.is_paused and (
            (self.now_playing_pos == 0 and len(self) == 1)
            or (self.now_playing_pos == len(self) - 1)
        ):
            # one track added to empty queue or new track added after queue end passed
            await self.player_manager.play(
                self.guild_id,
                track.encoded,
            )

    async def next(self) -> models.Track | None:
        """Move to the next track."""
        if not self.now_playing_pos < len(self):
            return None

        self.now_playing_pos += 1

        if not self.is_paused and self.now_playing_pos < len(self):
            assert self.now_playing
            await self.player_manager.play(
                self.guild_id,
                self.now_playing.encoded,
            )

        return self.now_playing

    async def previous(self) -> models.Track | None:
        if not self.now_playing_pos > 0:
            return None
        self.now_playing_pos -= 1

        if not self.is_paused:
            assert self.now_playing
            await self.player_manager.play(
                self.guild_id,
                self.now_playing.encoded,
            )

        return self.now_playing

    prev = previous

    def shuffle(self, mode: int) -> None:
        upcoming = self.queue[self.now_playing_pos + 1 :]
        history = self.queue[: self.now_playing_pos]
        if mode == 0:
            # independently shuffle upcoming and history with respect to now_playing_pos
            random.shuffle(upcoming)
            random.shuffle(history)
            self.queue[self.now_playing_pos + 1 :] = upcoming
            self.queue[: self.now_playing_pos] = history
        
        elif mode == 1:
            combined = upcoming + history
            random.shuffle(combined)
            self.queue[self.now_playing_pos + 1 :] = combined[self.now_playing_pos + 1 :]
            self.queue[: self.now_playing_pos] = combined[: self.now_playing_pos]

    async def skip_to(self, index: int) -> models.Track:
        if not 0 <= index < len(self.queue):
            raise IndexError

        self.now_playing_pos = index
        assert self.now_playing

        if not self.is_paused:
            await self.player_manager.play(
                self.guild_id,
                self.now_playing.encoded,
            )

        return self.now_playing

    play_at = skip_to

    def clear(self) -> None:
        self.queue.clear()