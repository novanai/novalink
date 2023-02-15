from __future__ import annotations

import abc
import datetime
import typing

import attr
import typing_extensions

import lavalink.models as models
import lavalink.types as types


class Event(models.BaseLavalinkModel, abc.ABC):
    ...


EventT = typing.TypeVar("EventT", bound=Event, contravariant=True)

EventsCallbackT = typing.Callable[[EventT], types.AwaitableNull]


@attr.define()
class ReadyEvent(Event):
    """Dispatched by Lavalink upon successful connection and authorization."""

    resumed: bool
    """Whether a session was resumed."""
    session_id: str
    """The Lavalink session ID of this connection."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        resumed = data["resumed"]
        session_id = data["sessionId"]

        assert isinstance(resumed, bool) and isinstance(session_id, str)
        return cls(resumed, session_id)


@attr.define()
class PlayerUpdateEvent(Event):
    """Dispatched every ``x`` seconds (configurable in `application.yml
    <https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example>`_)
    with the current state of the player."""

    guild_id: int
    """The guild ID of the player."""
    state: models.PlayerState
    """The player state."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        state = data["state"]

        assert (
            isinstance(guild_id, str) and guild_id.isdigit() and isinstance(state, dict)
        )
        return cls(int(guild_id), models.PlayerState.from_payload(state))


@attr.define()
class StatsEvent(models.Stats, Event):
    """A collection of stats dispatched every minute."""


@attr.define()
class TrackStartEvent(Event):
    """Dispatched when a track starts playing."""

    guild_id: int
    """The guild ID."""
    encoded_track: str
    """The base64 encoded track that started playing."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        encoded_track = data["encodedTrack"]

        assert (
            isinstance(guild_id, str)
            and guild_id.isdigit()
            and isinstance(encoded_track, str)
        )

        return cls(int(guild_id), encoded_track)


@attr.define()
class TrackEndEvent(Event):
    """Dispatched when a track ends."""

    guild_id: int
    """The guild ID."""
    encoded_track: str
    """The base64 encoded track that ended playing."""
    reason: models.TrackEndReason
    """The reason the track ended."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        encoded_track = data["encodedTrack"]
        reason = data["reason"]

        assert (
            isinstance(guild_id, str)
            and guild_id.isdigit()
            and isinstance(encoded_track, str)
            and isinstance(reason, str)
        )

        return cls(
            int(guild_id),
            encoded_track,
            models.TrackEndReason(reason),
        )


@attr.define()
class TrackExceptionEvent(Event):
    guild_id: int
    """The guild ID."""
    encoded_track: str
    """The base64 encoded track that threw the exception."""
    exception: models.TrackException
    """The exception that occurred."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        encoded_track = data["encodedTrack"]
        exception = data["exception"]

        assert (
            isinstance(guild_id, str)
            and guild_id.isdigit()
            and isinstance(encoded_track, str)
            and isinstance(exception, dict)
        )

        return cls(
            int(guild_id),
            encoded_track,
            models.TrackException.from_payload(exception),
        )


@attr.define()
class TrackStuckEvent(Event):
    guild_id: int
    """The guild ID."""
    encoded_track: str
    """The base64 encoded track that got stuck."""
    threshold: datetime.timedelta
    """The threshold that was exceeded."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        encoded_track = data["encodedTrack"]
        threshold_ms = data["thresholdMs"]

        assert (
            isinstance(guild_id, str)
            and guild_id.isdigit()
            and isinstance(encoded_track, str)
            and isinstance(threshold_ms, int)
        )

        return cls(
            int(guild_id),
            encoded_track,
            datetime.timedelta(milliseconds=threshold_ms),
        )


@attr.define()
class WebSocketClosedEvent(Event):
    guild_id: int
    """The guild ID."""
    code: int
    """The `Discord close event code
    <https://discord.com/developers/docs/topics/opcodes-and-status-codes#voice-voice-close-event-codes>`_"""
    reason: str
    """The close reason."""
    by_remote: bool
    """Whether the connection was closed by Discord."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        code = data["code"]
        reason = data["reason"]
        by_remote = data["byRemote"]

        assert (
            isinstance(guild_id, str)
            and guild_id.isdigit()
            and isinstance(code, int)
            and isinstance(reason, str)
            and isinstance(by_remote, bool)
        )

        return cls(
            int(guild_id),
            code,
            reason,
            by_remote,
        )
