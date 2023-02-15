from __future__ import annotations

import lavalink.client as client
import lavalink.ext.manager.queue as queue_


class PlayerManager:
    def __init__(self, lavalink: client.Lavalink) -> None:
        self.lavalink = lavalink
        self.queues: dict[int, queue_.Queue] = {}

    def get_queue(self, guild_id: int) -> queue_.Queue | None:
        if queue := self.queues.get(guild_id):
            return queue

    def create_queue(self, guild_id: int) -> queue_.Queue:
        queue = queue_.Queue(guild_id, self.lavalink, self)
        self.queues[guild_id] = queue
        return queue

    def get_or_create_queue(self, guild_id: int) -> queue_.Queue:
        if queue := self.get_queue(guild_id):
            return queue

        queue = self.create_queue(guild_id)
        return queue

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

    # NOTE: don't think we need this + if user stops the player, queue will skip to the
    # next track.
    # async def stop(self, guild_id: int) -> None:
    #     await self.lavalink.update_player(
    #         guild_id,
    #         encoded_track=None,
    #     )

    async def destroy(self, guild_id: int) -> None:
        await self.lavalink.destroy_player(guild_id)
        self.delete_queue(guild_id)
