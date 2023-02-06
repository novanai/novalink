from __future__ import annotations

import datetime
import enum

import attr


@attr.define()
class PlayerState:
    time: datetime.datetime
    position: datetime.timedelta
    connected: bool
    ping: datetime.timedelta

    @classmethod
    def from_payload(cls, data: dict) -> PlayerState:
        return cls(
            datetime.datetime.fromtimestamp(data["time"]),
            datetime.timedelta(milliseconds=data["position"]),
            data["connected"],
            datetime.timedelta(milliseconds=data["ping"]),
        )


@attr.define()
class Memory:
    free: int
    used: int
    allocated: int
    reservable: int

    @classmethod
    def from_payload(cls, data: dict) -> Memory:
        return cls(
            data["free"],
            data["used"],
            data["allocated"],
            data["reservable"],
        )


@attr.define()
class CPU:
    cores: int
    system_load: float
    lavalink_load: float

    @classmethod
    def from_payload(cls, data: dict) -> CPU:
        return cls(
            data["cores"],
            data["systemLoad"],
            data["lavalinkLoad"],
        )


@attr.define()
class FrameStats:
    sent: int
    nulled: int
    deficit: int

    @classmethod
    def from_payload(cls, data: dict) -> FrameStats:
        return cls(
            data["sent"],
            data["nulled"],
            data["deficit"],
        )


class TrackEndReason(enum.Enum):
    FINISHED = "FINISHED"
    LOAD_FAILED = "LOAD_FAILED"
    STOPPED = "STOPPED"
    REPLACED = "REPLACED"
    CLEANUP = "CLEANUP"


class ExceptionSeverity(enum.Enum):
    COMMON = "COMMON"
    SUSPICIOUS = "SUSPICIOUS"
    FATAL = "FATAL"


@attr.define()
class TrackException:
    message: str | None
    severity: ExceptionSeverity
    cause: str

    @classmethod
    def from_payload(cls, data: dict) -> TrackException:
        return cls(
            data["message"],
            ExceptionSeverity(data["severity"]),
            data["cause"],
        )


@attr.define()
class Player:
    guild_id: int
    track: Track | None
    volume: int
    paused: bool
    voice: VoiceState
    filters: Filters

    @classmethod
    def from_payload(cls, data: dict) -> Player:
        return cls(
            int(data["guildId"]),
            Track.from_payload(t) if (t := data["track"]) else None,
            data["volume"],
            data["paused"],
            VoiceState.from_payload(data["voice"]),
            Filters.from_payload(data["filters"]),
        )


@attr.define()
class Track:
    encoded: str
    info: TrackInfo

    @classmethod
    def from_payload(cls, data: dict) -> Track:
        return cls(data["encoded"], TrackInfo.from_payload(data["info"]))


@attr.define()
class TrackInfo:
    identifier: str
    is_seekable: bool
    author: str
    length: datetime.timedelta
    is_stream: bool
    position: datetime.timedelta
    title: str
    uri: str | None
    source_name: str

    @classmethod
    def from_payload(cls, data: dict) -> TrackInfo:
        return cls(
            data["identifier"],
            data["isSeekable"],
            data["author"],
            datetime.timedelta(milliseconds=data["length"]),
            data["isStream"],
            datetime.timedelta(milliseconds=data["position"]),
            data["title"],
            data["uri"],
            data["sourceName"],
        )


@attr.define()
class VoiceState:
    token: str
    endpoint: str
    session_id: str
    connected: bool | None
    ping: int | None

    @classmethod
    def from_payload(cls, data: dict) -> VoiceState:
        return cls(
            data["token"],
            data["endpoint"],
            data["sessionId"],
            data.get("connected"),
            data.get("ping"),
        )


@attr.define()
class Filters:
    volume: float | None
    equalizer: list[Equalizer] | None
    karaoke: Karaoke | None
    timescale: Timescale | None
    tremolo: Tremolo | None
    vibrato: Vibrato | None
    rotation: Rotation | None
    distortion: Distortion | None
    channel_mix: ChannelMix | None
    low_pass: LowPass | None

    @classmethod
    def from_payload(cls, data: dict) -> Filters:
        return cls(
            data.get("volume"),
            [Equalizer.from_payload(thing) for thing in e]
            if (e := data.get("equalizer"))
            else None,
            Karaoke.from_payload(t) if (t := data.get("karaoke")) else None,
            Timescale.from_payload(t) if (t := data.get("timescale")) else None,
            Tremolo.from_payload(t) if (t := data.get("tremolo")) else None,
            Vibrato.from_payload(t) if (t := data.get("vibrato")) else None,
            Rotation.from_payload(t) if (t := data.get("rotation")) else None,
            Distortion.from_payload(t) if (t := data.get("distortion")) else None,
            ChannelMix.from_payload(t) if (t := data.get("channelMix")) else None,
            LowPass.from_payload(t) if (t := data.get("lowPass")) else None,
        )


@attr.define()
class Equalizer:
    band: int
    gain: float

    @classmethod
    def from_payload(cls, data: dict) -> Equalizer:
        return cls(data["band"], data["gain"])


@attr.define()
class Karaoke:
    level: float | None
    mono_level: float | None
    filter_band: float | None
    filter_width: float | None

    @classmethod
    def from_payload(cls, data: dict) -> Karaoke:
        return cls(
            data.get("level"),
            data.get("monoLevel"),
            data.get("filterBand"),
            data.get("filterWidth"),
        )


@attr.define()
class Timescale:
    speed: float | None
    pitch: float | None
    rate: float | None

    @classmethod
    def from_payload(cls, data: dict) -> Timescale:
        return cls(
            data.get("speed"),
            data.get("pitch"),
            data.get("rate"),
        )


@attr.define()
class Tremolo:
    frequency: float | None
    depth: float | None

    @classmethod
    def from_payload(cls, data: dict) -> Tremolo:
        return cls(
            data.get("frequency"),
            data.get("depth"),
        )


@attr.define()
class Vibrato:
    frequency: float | None
    depth: float | None

    @classmethod
    def from_payload(cls, data: dict) -> Vibrato:
        return cls(
            data.get("frequency"),
            data.get("depth"),
        )


@attr.define()
class Rotation:
    rotation_hz: float | None

    @classmethod
    def from_payload(cls, data: dict) -> Rotation:
        return cls(
            data.get("rotationHz"),
        )


@attr.define()
class Distortion:
    sin_offset: float | None
    sin_scale: float | None
    cos_offset: float | None
    cos_scale: float | None
    tan_offset: float | None
    tan_scale: float | None
    offset: float | None
    scale: float | None

    @classmethod
    def from_payload(cls, data: dict) -> Distortion:
        return cls(
            data.get("sinOffset"),
            data.get("sinScale"),
            data.get("cosOffset"),
            data.get("cosScale"),
            data.get("tanOffset"),
            data.get("tanScale"),
            data.get("offset"),
            data.get("scale"),
        )


@attr.define()
class ChannelMix:
    left_to_left: float | None
    left_to_right: float | None
    right_to_left: float | None
    right_to_right: float | None

    @classmethod
    def from_payload(cls, data: dict) -> ChannelMix:
        return cls(
            data.get("leftToLeft"),
            data.get("leftToRight"),
            data.get("rightToLeft"),
            data.get("rightToRight"),
        )


@attr.define()
class LowPass:
    smoothing: float | None

    @classmethod
    def from_payload(cls, data: dict) -> LowPass:
        return cls(
            data.get("smoothing"),
        )
