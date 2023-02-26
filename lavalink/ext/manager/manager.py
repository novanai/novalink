from __future__ import annotations

import datetime

import lavalink.client as client
import lavalink.ext.manager.errors as errors
import lavalink.ext.manager.models as ext_models
import lavalink.ext.manager.queue as queue_
import lavalink.models as models


class PlayerManager:
    def __init__(self, lavalink: client.Lavalink) -> None:
        self.lavalink = lavalink
        self.queues: dict[int, queue_.Queue] = {}

    def get_queue(self, guild_id: int) -> queue_.Queue | None:
        return self.queues.get(guild_id)

    def create_queue(self, guild_id: int) -> queue_.Queue:
        if self.get_queue(guild_id):
            raise errors.QueueAlreadyExists(
                f"A queue already exists for guild with ID {guild_id}"
            )

        queue = queue_.Queue(guild_id, self.lavalink, self)
        self.queues[guild_id] = queue
        return queue

    def get_or_create_queue(self, guild_id: int) -> queue_.Queue:
        return self.get_queue(guild_id) or self.create_queue(guild_id)

    def delete_queue(self, guild_id: int) -> None:
        del self.queues[guild_id]

    async def play(self, guild_id: int, encoded_track: str) -> None:
        await self.lavalink.update_player(
            guild_id,
            encoded_track=encoded_track,
        )

    async def pause(self, guild_id: int) -> None:
        await self.lavalink.update_player(
            guild_id,
            paused=True,
        )

        if queue := self.get_queue(guild_id):
            queue.is_paused = True

    async def resume(self, guild_id: int) -> None:
        await self.lavalink.update_player(
            guild_id,
            paused=False,
        )

        if queue := self.get_queue(guild_id):
            queue.is_paused = False

    async def next(self, guild_id: int) -> models.Track | None:
        """Move to the next track."""
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        if not queue.now_playing_pos < len(queue.queue):
            return None

        queue.now_playing_pos += 1

        if not queue.is_paused and queue.now_playing_pos < len(queue.queue):
            assert queue.now_playing
            await self.play(
                guild_id,
                queue.now_playing.encoded,
            )

        return queue.now_playing

    async def previous(self, guild_id: int) -> models.Track | None:
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        if not queue.now_playing_pos > 0:
            return None
        queue.now_playing_pos -= 1

        if not queue.is_paused:
            assert queue.now_playing
            await self.play(
                guild_id,
                queue.now_playing.encoded,
            )

        return queue.now_playing

    prev = previous

    async def skip_to(self, guild_id: int, index: int) -> models.Track | None:
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        if not 0 <= index <= len(queue.queue):
            raise IndexError

        queue.now_playing_pos = index

        if not queue.is_paused:
            if queue.now_playing:
                await self.play(
                    guild_id,
                    queue.now_playing.encoded,
                )
            else:
                await self.stop(guild_id)

        return queue.now_playing

    play_at = skip_to

    async def seek_to(self, guild_id: int, position: datetime.timedelta) -> None:
        await self.lavalink.update_player(guild_id, position=position)

    async def stop(self, guild_id: int) -> None:
        await self.lavalink.update_player(
            guild_id,
            encoded_track=None,
        )

    async def destroy(self, guild_id: int) -> None:
        await self.lavalink.destroy_player(guild_id)
        self.delete_queue(guild_id)

    async def set_volume(self, guild_id: int, volume: int) -> None:
        await self.lavalink.update_player(guild_id, volume=volume)

    async def set_filters(self, guild_id: int, filters: models.Filters) -> None:
        await self.lavalink.update_player(guild_id, filters=filters)

    def set_repeat_mode(self, guild_id: int, mode: ext_models.RepeatMode) -> None:
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        queue.repeat_mode = mode
