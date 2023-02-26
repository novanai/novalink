from __future__ import annotations

import random
import typing

import lavalink.client as client
import lavalink.events as events
import lavalink.ext.manager.models as ext_models
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
        self.repeat_mode: ext_models.RepeatMode = ext_models.RepeatMode.NONE

        for event in (
            events.TrackEndEvent,
            events.TrackStuckEvent,
            events.TrackExceptionEvent,
        ):
            lavalink.listen(event, self.track_events)

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
        if event.guild_id != self.guild_id or self.is_paused:
            return

        if (
            isinstance(event, events.TrackEndEvent)
            and event.reason is not models.TrackEndReason.FINISHED
        ):
            return

        if self.repeat_mode is ext_models.RepeatMode.ONE:
            await self.player_manager.play(
                self.guild_id,
                event.encoded_track,
            )
        elif (
            self.repeat_mode is ext_models.RepeatMode.ALL
            and self.now_playing_pos >= len(self.queue)
        ):
            await self.player_manager.skip_to(self.guild_id, 0)
        else:
            await self.player_manager.next(event.guild_id)

    async def add(self, track: models.Track) -> None:
        self.queue.append(track)

        if not self.is_paused and (
            (self.now_playing_pos == 0 and len(self.queue) == 1)
            or (self.now_playing_pos == len(self.queue) - 1)
        ):
            # one track added to empty queue or new track added after queue end passed
            await self.player_manager.play(
                self.guild_id,
                track.encoded,
            )

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
            # shuffle whole queue
            combined = upcoming + history
            random.shuffle(combined)
            self.queue[self.now_playing_pos + 1 :] = combined[
                self.now_playing_pos + 1 :
            ]
            self.queue[: self.now_playing_pos] = combined[: self.now_playing_pos]

    def clear(self) -> None:
        self.queue.clear()

    @typing.overload
    def remove_tracks(self, *tracks: models.Track) -> None:
        ...

    @typing.overload
    def remove_tracks(self, *indexes: int) -> None:
        ...

    def remove_tracks(self, *tracks_or_indexes: models.Track | int) -> None:
        for item in tracks_or_indexes:
            if isinstance(item, models.Track):
                self.queue.remove(item)
            else:
                self.queue.pop(item)
