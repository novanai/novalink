from __future__ import annotations

import abc
import datetime
import typing

import attr
import typing_extensions

from . import models
from .types import PayloadType


class Event(models.BaseLavalinkModel, abc.ABC):
    ...


EventT = typing.TypeVar("EventT", bound=Event, contravariant=True)

EventsCallbackT = typing.Callable[[EventT], typing.Awaitable[typing.Any]]


@attr.define()
class ReadyEvent(Event):
    resumed: bool
    session_id: str

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        resumed = data["resumed"]
        session_id = data["sessionId"]

        assert isinstance(resumed, bool) and isinstance(session_id, str)
        return cls(resumed, session_id)


@attr.define()
class PlayerUpdateEvent(Event):
    guild_id: int
    state: models.PlayerState

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        state = data["state"]

        assert (
            isinstance(guild_id, str) and guild_id.isdigit() and isinstance(state, dict)
        )
        return cls(int(guild_id), models.PlayerState.from_payload(state))


@attr.define()
class StatsEvent(models.Stats, Event):
    ...


@attr.define()
class TrackStartEvent(Event):
    guild_id: int
    encoded_track: str

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
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
    guild_id: int
    encoded_track: str
    reason: models.TrackEndReason

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
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
    encoded_track: str
    exception: models.TrackException

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
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
    encoded_track: str
    threshold: datetime.timedelta

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
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
    code: int
    reason: str
    by_remote: bool

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
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
