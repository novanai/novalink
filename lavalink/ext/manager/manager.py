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
        """Get a queue.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get the queue for.
        """
        return self.queues.get(guild_id)

    def create_queue(self, guild_id: int) -> queue_.Queue:
        """Create a queue.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to create the queue for.

        Raises
        ------
        errors.QueueAlreadyExists
            When a queue already exists for the guild.
        """
        if self.get_queue(guild_id):
            raise errors.QueueAlreadyExists(
                f"A queue already exists for guild with ID {guild_id}"
            )

        queue = queue_.Queue(guild_id, self.lavalink, self)
        self.queues[guild_id] = queue
        return queue

    def get_or_create_queue(self, guild_id: int) -> queue_.Queue:
        """Get an existing queue or create a new one.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get or create the queue for.
        """
        return self.get_queue(guild_id) or self.create_queue(guild_id)

    def delete_queue(self, guild_id: int) -> None:
        """Delete a queue.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to delete the queue for.
        """
        del self.queues[guild_id]

    async def play(self, guild_id: int, encoded_track: str) -> None:
        """Play a track in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to play the track in.
        encoded_track : str
            The base64 encoded track to play.
        """
        await self.lavalink.update_player(
            guild_id,
            encoded_track=encoded_track,
        )

    async def pause(self, guild_id: int) -> None:
        """Pause the player in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to pause the player for.
        """
        await self.lavalink.update_player(
            guild_id,
            paused=True,
        )

        if queue := self.get_queue(guild_id):
            queue.is_paused = True

    async def resume(self, guild_id: int) -> None:
        """Resume the player in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to resume the player for.
        """
        await self.lavalink.update_player(
            guild_id,
            paused=False,
        )

        if queue := self.get_queue(guild_id):
            queue.is_paused = False

    async def next(self, guild_id: int) -> models.Track | None:
        """Move to the next track in the queue.

        .. note::

            Stops playing if the end of the queue is reached.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        models.Track
            The track that just started playing, if any.

        Raises
        ------
        errors.QueueNotFound
            If a queue was not found for the guild.
        """
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        if queue.now_playing_pos >= len(queue.queue):  # don't move beyond last track
            return None

        return await self.skip_to(guild_id, queue.now_playing_pos + 1)

    async def previous(self, guild_id: int) -> models.Track | None:
        """Move to the previous track in the queue.

        .. note::

            Does not move beyond the first track in the queue.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        models.Track
            The track that just started playing, if any.

        Raises
        ------
        errors.QueueNotFound
            If a queue was not found for the guild.
        """
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        if queue.now_playing_pos <= 0:  # don't move beyond first track
            return None

        return await self.skip_to(guild_id, queue.now_playing_pos - 1)

    prev = previous
    """An alias for :func:`PlayerManager.previous`"""

    async def skip_to(self, guild_id: int, index: int) -> models.Track | None:
        """Skip to a track track in the queue.

        .. note::

            Does not move beyond the first track in the queue.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        models.Track
            The track that just started playing, if any.

        Raises
        ------
        errors.QueueNotFound
            If a queue was not found for the guild.
        IndexError
            If the index is out of the range ``0 <= index <= queue length``.
        """
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        if not 0 <= index <= len(queue.queue):
            raise IndexError("Index must be in range `0 <= index <= queue length`")

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
    """An alias for :func:`PlayerManager.skip_to`"""

    async def seek_to(self, guild_id: int, position: datetime.timedelta) -> None:
        """Seek to a position in the current track.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        position : datetime.timedelta
            The position to seek to.
        """
        await self.lavalink.update_player(guild_id, position=position)

    async def stop(self, guild_id: int) -> None:
        """Stop the current track.

        .. note::
            This is **not** an alias for `pause`, you will not be able to resume the track.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        """
        await self.lavalink.update_player(
            guild_id,
            encoded_track=None,
        )

    async def destroy(self, guild_id: int) -> None:
        """Destroy a guild's player and queue.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        """
        await self.lavalink.destroy_player(guild_id)
        self.delete_queue(guild_id)

    async def set_volume(self, guild_id: int, volume: int) -> None:
        """Set a player's volume.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        volume : int
            Volume in percentage, from 0 - 1000.
        """
        await self.lavalink.update_player(guild_id, volume=volume)

    async def set_filters(self, guild_id: int, filters: models.Filters) -> None:
        """Set a player's filters.

        .. note::
            This will override all previously applied filters.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        filter: models.Filters
            The new filters to apply.
        """
        await self.lavalink.update_player(guild_id, filters=filters)

    def set_repeat_mode(self, guild_id: int, mode: ext_models.RepeatMode) -> None:
        """Set a queue's repeat mode.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        mode : ext_models.RepeatMode
            The repeat mode.

        Raises
        ------
        errors.QueueNotFound
            If a queue was not found for the guild.
        """
        queue = self.get_queue(guild_id)
        if not queue:
            raise errors.QueueNotFound(f"Queue not found for guild with ID {guild_id}")

        queue.repeat_mode = mode
