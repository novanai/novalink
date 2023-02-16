from __future__ import annotations

import lavalink.client as client
import lavalink.ext.manager.queue as queue_


class PlayerManager:
    def __init__(self, lavalink: client.Lavalink) -> None:
        self.lavalink = lavalink
        self.queues: dict[int, queue_.Queue] = {}

    def get_queue(self, guild_id: int) -> queue_.Queue | None:
        return self.queues.get(guild_id) 

    def create_queue(self, guild_id: int) -> queue_.Queue:
        if self.get_queue(guild_id):
            raise ValueError("A queue already exists for this guild.")

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

    async def stop(self, guild_id: int) -> None:
        await self.lavalink.update_player(
            guild_id,
            encoded_track=None,
        )

    async def destroy(self, guild_id: int) -> None:
        await self.lavalink.destroy_player(guild_id)
        self.delete_queue(guild_id)
