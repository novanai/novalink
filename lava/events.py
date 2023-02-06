from __future__ import annotations

import abc
import datetime
import typing

import attr

from lava import models


class Event(abc.ABC):
    @abc.abstractmethod
    def from_payload(cls, data: dict) -> Event:
        ...


EventT = typing.TypeVar("EventT", bound=Event)

EventsCallbackT = typing.Callable[[EventT], typing.Awaitable[typing.Any]]


@attr.define()
class ReadyEvent(Event):
    resumed: bool
    session_id: str

    @classmethod
    def from_payload(cls, data: dict) -> ReadyEvent:
        return cls(data["resumed"], data["sessionId"])


@attr.define()
class PlayerUpdateEvent(Event):
    guild_id: int
    state: models.PlayerState

    @classmethod
    def from_payload(cls, data: dict) -> PlayerUpdateEvent:
        return cls(int(data["guildId"]), models.PlayerState.from_payload(data["state"]))


@attr.define()
class StatsEvent(Event):
    players: int
    playing_players: int
    uptime: datetime.timedelta
    memory: models.Memory
    cpu: models.CPU
    frame_stats: models.FrameStats | None

    @classmethod
    def from_payload(cls, data: dict) -> StatsEvent:
        return cls(
            data["players"],
            data["playingPlayers"],
            datetime.timedelta(milliseconds=data["uptime"]),
            models.Memory.from_payload(data["memory"]),
            models.CPU.from_payload(data["cpu"]),
            models.FrameStats.from_payload(f)
            if (f := data.get("frameStats"))
            else None,
        )


@attr.define()
class TrackStartEvent(Event):
    guild_id: int
    encoded_track: str

    @property
    def track(self) -> ...:
        ...

    @classmethod
    def from_payload(cls, data: dict) -> TrackStartEvent:
        return cls(
            int(data["guildId"]),
            data["encodedTrack"],
        )


@attr.define()
class TrackEndEvent(Event):
    guild_id: int
    encoded_track: str
    reason: models.TrackEndReason

    @property
    def track(self) -> ...:
        ...

    @classmethod
    def from_payload(cls, data: dict) -> TrackEndEvent:
        return cls(
            int(data["guildId"]),
            data["encodedTrack"],
            models.TrackEndReason(data["reason"]),
        )


@attr.define()
class TrackExceptionEvent(Event):
    guild_id: int
    encoded_track: str
    exception: models.TrackException

    @property
    def track(self) -> ...:
        ...

    @classmethod
    def from_payload(cls, data: dict) -> TrackExceptionEvent:
        return cls(
            int(data["guildId"]),
            data["encodedTrack"],
            models.TrackException.from_payload(data["exception"]),
        )


@attr.define()
class TrackStuckEvent(Event):
    guild_id: int
    encoded_track: str
    threshold: datetime.timedelta

    @classmethod
    def from_payload(cls, data: dict) -> TrackStuckEvent:
        return cls(
            int(data["guildId"]),
            data["track"],
            datetime.timedelta(milliseconds=data["thresholdMs"]),
        )


@attr.define
class WebSocketClosedEvent(Event):
    guild_id: int
    code: int
    reason: str
    by_remote: bool

    @classmethod
    def from_payload(cls, data: dict) -> WebSocketClosedEvent:
        return cls(
            int(data["guildId"]),
            data["code"],
            data["reason"],
            data["byRemote"],
        )
