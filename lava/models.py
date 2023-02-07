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
            datetime.datetime.fromtimestamp(data["time"] / 1000),
            datetime.timedelta(milliseconds=data["position"]),
            data["connected"],
            datetime.timedelta(milliseconds=data["ping"]),
        )


@attr.define()
class Stats:
    players: int
    playing_players: int
    uptime: datetime.timedelta
    memory: Memory
    cpu: CPU
    frame_stats: FrameStats | None

    @classmethod
    def from_payload(cls, data: dict) -> Stats:
        return cls(
            data["players"],
            data["playingPlayers"],
            datetime.timedelta(milliseconds=data["uptime"]),
            Memory.from_payload(data["memory"]),
            CPU.from_payload(data["cpu"]),
            FrameStats.from_payload(f) if (f := data.get("frameStats")) else None,
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

    def to_payload(self) -> dict:
        return {
            "token": self.token,
            "endpoint": self.endpoint,
            "sessionId": self.session_id,
            "connected": self.connected,
            "ping": self.ping,
        }


@attr.define()
class Filters:
    volume: float | None
    equalizers: list[Equalizer] | None
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

    def to_payload(self) -> dict:
        return {
            "volume": self.volume,
            "equalizer": [attr.asdict(e) for e in self.equalizers]
            if self.equalizers
            else None,
            "karaoke": self.karaoke.to_payload() if self.karaoke else None,
            "timescale": attr.asdict(self.timescale) if self.timescale else None,
            "tremolo": attr.asdict(self.tremolo) if self.tremolo else None,
            "vibrato": attr.asdict(self.vibrato) if self.vibrato else None,
            "rotation": self.rotation.to_payload() if self.rotation else None,
            "distortion": self.distortion.to_payload() if self.distortion else None,
            "channelMix": self.channel_mix.to_payload() if self.channel_mix else None,
            "lowPass": attr.asdict(self.low_pass) if self.low_pass else None,
        }


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

    def to_payload(self) -> dict:
        return {
            "level": self.level,
            "monoLevel": self.mono_level,
            "filterBand": self.filter_band,
            "filterWidth": self.filter_width,
        }


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

    def to_payload(self) -> dict:
        return {"rotationHz": self.rotation_hz}


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

    def to_payload(self) -> dict:
        return {
            "sinOffset": self.sin_offset,
            "sinScale": self.sin_scale,
            "cosOffset": self.cos_offset,
            "cosScale": self.cos_scale,
            "tanOffset": self.tan_offset,
            "tanScale": self.tan_scale,
            "offset": self.offset,
            "scale": self.scale,
        }


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

    def to_payload(self) -> dict:
        return {
            "leftToLeft": self.left_to_left,
            "leftToRight": self.left_to_right,
            "rightToLeft": self.right_to_left,
            "rightToRight": self.right_to_right,
        }


@attr.define()
class LowPass:
    smoothing: float | None

    @classmethod
    def from_payload(cls, data: dict) -> LowPass:
        return cls(
            data.get("smoothing"),
        )


@attr.define()
class LoadTrackResult:
    load_type: LoadResultType
    playlist_info: PlaylistInfo | None
    tracks: list[Track] | None
    exception: TrackException | None

    @classmethod
    def from_payload(cls, data: dict) -> LoadTrackResult:
        return cls(
            LoadResultType(data["loadType"]),
            PlaylistInfo.from_payload(d)
            if (d := data["playlistInfo"])
            else None,  # object will always be there but may be empty.
            [Track.from_payload(t) for t in tracks]
            if (tracks := data["tracks"])
            else None,  # object will always be there but may be empty.
            TrackException.from_payload(e) if (e := data.get("exception")) else None,
        )


class LoadResultType(enum.Enum):
    TRACK_LOADED = "TRACK_LOADED"
    PLAYLIST_LOADED = "PLAYLIST_LOADED"
    SEARCH_RESULT = "SEARCH_RESULT"
    NO_MATCHES = "NO_MATCHES"
    LOAD_FAILED = "LOAD_FAILED"


@attr.define()
class PlaylistInfo:
    name: str | None
    selected_track: int | None

    @classmethod
    def from_payload(cls, data: dict) -> PlaylistInfo:
        return cls(
            data.get("name"),
            data.get("selectedTrack"),
        )


@attr.define()
class LavalinkInfo:
    version: Version
    build_time: datetime.datetime
    git: Git
    jvm: str
    lavaplayer: str
    source_managers: list[str]
    filters: list[str]
    plugins: list[Plugin]

    @classmethod
    def from_payload(cls, data: dict) -> LavalinkInfo:
        return cls(
            Version.from_payload(data["version"]),
            datetime.datetime.fromtimestamp(data["buildTime"] / 1000),
            Git.from_payload(data["git"]),
            data["jvm"],
            data["lavaplayer"],
            data["sourceManagers"],
            data["filters"],
            [Plugin.from_payload(p) for p in data["plugins"]],
        )


@attr.define()
class Version:
    semver: str
    major: int
    minor: int
    patch: int
    pre_release: str | None

    @classmethod
    def from_payload(cls, data: dict) -> Version:
        return cls(
            data["semver"],
            data["major"],
            data["minor"],
            data["patch"],
            data["preRelease"],
        )


@attr.define()
class Git:
    branch: str
    commit: str
    commit_time: datetime.datetime

    @classmethod
    def from_payload(cls, data: dict) -> Git:
        return cls(
            data["branch"],
            data["commit"],
            datetime.datetime.fromtimestamp(data["commitTime"] / 1000),
        )


@attr.define()
class Plugin:
    name: str
    version: str

    @classmethod
    def from_payload(cls, data: dict) -> Plugin:
        return cls(
            data["name"],
            data["version"],
        )


@attr.define()
class RoutePlannerStatus:
    _type: RoutePlannerType
    details: Details | None

    @property
    def type(self) -> RoutePlannerType:
        return self._type

    @classmethod
    def from_payload(cls, data: dict) -> RoutePlannerStatus:
        return cls(
            RoutePlannerType(data["class"]),
            Details.from_payload(d) if (d := data["details"]) else None,
        )


class RoutePlannerType(enum.Enum):
    ROTATING_IP_ROUTE_PLANNER = "RotatingIpRoutePlanner"
    NANO_IP_ROUTE_PLANNER = "NanoIpRoutePlanner"
    ROTATING_NANO_IP_ROUTE_PLANNER = "RotatingNanoIpRoutePlanner"
    BALANCING_IP_ROUTE_PLANNER = "BalancingIpRoutePlanner"


@attr.define()
class Details:
    ip_block: IPBlock
    failing_addresses: list[FailingAddress]
    rotate_index: str
    ip_index: str
    current_address: str
    current_address_index: str
    block_index: str

    @classmethod
    def from_payload(cls, data: dict) -> Details:
        return cls(
            IPBlock.from_payload(data["ipBlock"]),
            [FailingAddress.from_payload(a) for a in data["failingAddresses"]],
            data["rotateIndex"],
            data["ipIndex"],
            data["currentAddress"],
            data["currentAddressIndex"],
            data["blockIndex"],
        )


@attr.define()
class IPBlock:
    _type: IPBlockType
    size: str

    @property
    def type(self) -> IPBlockType:
        return self._type

    @classmethod
    def from_payload(cls, data: dict) -> IPBlock:
        return cls(
            IPBlockType(data["type"]),
            data["size"],
        )


class IPBlockType(enum.Enum):
    INET_4_ADDRESS = "Inet4Address"
    INET_6_ADDRESS = "Inet6Address"


@attr.define()
class FailingAddress:
    address: str
    failing_time: datetime.datetime

    @classmethod
    def from_payload(cls, data: dict) -> FailingAddress:
        return cls(
            data["address"],
            datetime.datetime.fromtimestamp(data["failingTimestamp"] / 1000),
        )
