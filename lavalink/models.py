from __future__ import annotations

import abc
import datetime
import enum
import typing

import attr
import typing_extensions

from .types import (PayloadType, is_payload_list, is_payload_list_nullable,
                    is_str_list)


class BaseLavalinkModel(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        ...

    @classmethod
    def from_payloads(
        cls, data: typing.Iterable[PayloadType]
    ) -> tuple[typing_extensions.Self]:
        return tuple(cls.from_payload(d) for d in data)

    @typing.overload
    @classmethod
    def from_payload_nullable(cls, data: PayloadType) -> typing_extensions.Self:
        ...

    @typing.overload
    @classmethod
    def from_payload_nullable(cls, data: None) -> None:
        ...

    @classmethod
    def from_payload_nullable(
        cls, data: PayloadType | None
    ) -> typing_extensions.Self | None:
        return cls.from_payload(data) if data is not None else None

    @typing.overload
    @classmethod
    def from_payloads_nullable(
        cls, data: typing.Iterable[PayloadType]
    ) -> tuple[typing_extensions.Self]:
        ...

    @typing.overload
    @classmethod
    def from_payloads_nullable(cls, data: None) -> None:
        ...

    @classmethod
    def from_payloads_nullable(
        cls, data: typing.Iterable[PayloadType] | None
    ) -> tuple[typing_extensions.Self] | None:
        return tuple(cls.from_payload(d) for d in data) if data is not None else None


@attr.define()
class PlayerState(BaseLavalinkModel):
    time: datetime.datetime
    position: datetime.timedelta | None
    connected: bool
    ping: datetime.timedelta | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        time = data["time"]
        position = data.get("position")
        connected = data["connected"]
        ping = data["ping"]

        assert (
            isinstance(time, int)
            and isinstance(position, int | None)
            and isinstance(connected, bool)
            and isinstance(ping, int)
        )

        return cls(
            datetime.datetime.fromtimestamp(time / 1000),
            datetime.timedelta(milliseconds=position) if position else None,
            connected,
            datetime.timedelta(milliseconds=ping) if ping != -1 else None,
        )


@attr.define()
class Stats(BaseLavalinkModel):
    players: int
    playing_players: int
    uptime: datetime.timedelta
    memory: Memory
    cpu: CPU
    frame_stats: FrameStats | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        players = data["players"]
        playing_players = data["playingPlayers"]
        uptime = data["uptime"]
        memory = data["memory"]
        cpu = data["cpu"]
        frame_stats = data.get("frameStats")

        assert (
            isinstance(players, int)
            and isinstance(playing_players, int)
            and isinstance(uptime, int)
            and isinstance(memory, dict)
            and isinstance(cpu, dict)
            and isinstance(frame_stats, dict | None)
        )

        return cls(
            players,
            playing_players,
            datetime.timedelta(milliseconds=uptime),
            Memory.from_payload(memory),
            CPU.from_payload(cpu),
            FrameStats.from_payload_nullable(frame_stats),
        )


@attr.define()
class Memory:
    free: int
    used: int
    allocated: int
    reservable: int

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        free = data["free"]
        used = data["used"]
        allocated = data["allocated"]
        reservable = data["reservable"]

        assert (
            isinstance(free, int)
            and isinstance(used, int)
            and isinstance(allocated, int)
            and isinstance(reservable, int)
        )

        return cls(free, used, allocated, reservable)


@attr.define()
class CPU(BaseLavalinkModel):
    cores: int
    system_load: float
    lavalink_load: float

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        cores = data["cores"]
        system_load = data["systemLoad"]
        lavalink_load = data["lavalinkLoad"]

        assert (
            isinstance(cores, int)
            and isinstance(system_load, float)
            and isinstance(lavalink_load, float)
        )

        return cls(cores, system_load, lavalink_load)


@attr.define()
class FrameStats(BaseLavalinkModel):
    sent: int
    nulled: int
    deficit: int

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        sent = data["sent"]
        nulled = data["nulled"]
        deficit = data["deficit"]

        assert (
            isinstance(sent, int)
            and isinstance(nulled, int)
            and isinstance(deficit, int)
        )

        return cls(sent, nulled, deficit)


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
class TrackException(BaseLavalinkModel):
    message: str | None
    severity: ExceptionSeverity
    cause: str

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        message = data["message"]
        severity = data["severity"]
        cause = data["cause"]

        assert (
            isinstance(message, str | None)
            and isinstance(severity, str)
            and isinstance(cause, str)
        )

        return cls(message, ExceptionSeverity(severity), cause)


@attr.define()
class Player(BaseLavalinkModel):
    guild_id: int
    track: Track | None
    volume: int
    paused: bool
    voice: VoiceState
    filters: Filters

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        guild_id = data["guildId"]
        track = data["track"]
        volume = data["volume"]
        paused = data["paused"]
        voice = data["voice"]
        filters = data["filters"]

        assert (
            isinstance(guild_id, str)
            and guild_id.isdigit()
            and isinstance(track, dict | None)
            and isinstance(volume, int)
            and isinstance(paused, bool)
            and isinstance(voice, dict)
            and isinstance(filters, dict)
        )

        return cls(
            int(guild_id),
            Track.from_payload_nullable(track),
            volume,
            paused,
            VoiceState.from_payload(voice),
            Filters.from_payload(filters),
        )


@attr.define()
class Track(BaseLavalinkModel):
    encoded: str
    info: TrackInfo

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        encoded = data["encoded"]
        info = data["info"]

        assert isinstance(encoded, str) and isinstance(info, dict)

        return cls(encoded, TrackInfo.from_payload(info))


@attr.define()
class TrackInfo(BaseLavalinkModel):
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
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        identifier = data["identifier"]
        is_seekable = data["isSeekable"]
        author = data["author"]
        length = data["length"]
        is_stream = data["isStream"]
        position = data["position"]
        title = data["title"]
        uri = data["uri"]
        source_name = data["sourceName"]

        assert (
            isinstance(identifier, str)
            and isinstance(is_seekable, bool)
            and isinstance(author, str)
            and isinstance(length, int)
            and isinstance(is_stream, bool)
            and isinstance(position, int)
            and isinstance(title, str)
            and isinstance(uri, str | None)
            and isinstance(source_name, str)
        )

        return cls(
            identifier,
            is_seekable,
            author,
            datetime.timedelta(milliseconds=length),
            is_stream,
            datetime.timedelta(milliseconds=position),
            title,
            uri,
            source_name,
        )


@attr.define()
class VoiceState(BaseLavalinkModel):
    token: str
    endpoint: str
    session_id: str
    connected: bool | None = None
    ping: int | None = None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        token = data["token"]
        endpoint = data["endpoint"]
        session_id = data["sessionId"]
        connected = data.get("connected")
        ping = data.get("ping")

        assert (
            isinstance(token, str)
            and isinstance(endpoint, str)
            and isinstance(session_id, str)
            and isinstance(connected, bool | None)
            and isinstance(ping, int | None)
        )

        return cls(
            token,
            endpoint,
            session_id,
            connected,
            ping,
        )

    def to_payload(self) -> PayloadType:
        return {
            "token": self.token,
            "endpoint": self.endpoint,
            "sessionId": self.session_id,
            "connected": self.connected,
            "ping": self.ping,
        }


@attr.define()
class Filters(BaseLavalinkModel):
    volume: float | None = None
    equalizers: tuple[Equalizer] | None = None
    karaoke: Karaoke | None = None
    timescale: Timescale | None = None
    tremolo: Tremolo | None = None
    vibrato: Vibrato | None = None
    rotation: Rotation | None = None
    distortion: Distortion | None = None
    channel_mix: ChannelMix | None = None
    low_pass: LowPass | None = None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        volume = data.get("volume")
        equalizers = data.get("equalizers")
        karaoke = data.get("karaoke")
        timescale = data.get("timescale")
        tremolo = data.get("tremolo")
        vibrato = data.get("vibrato")
        rotation = data.get("rotation")
        distortion = data.get("distortion")
        channel_mix = data.get("channelMix")
        low_pass = data.get("lowPass")

        assert (
            isinstance(volume, float | None)
            and isinstance(equalizers, list | None)
            and is_payload_list_nullable(equalizers)
            and isinstance(karaoke, dict | None)
            and isinstance(timescale, dict | None)
            and isinstance(tremolo, dict | None)
            and isinstance(vibrato, dict | None)
            and isinstance(rotation, dict | None)
            and isinstance(distortion, dict | None)
            and isinstance(channel_mix, dict | None)
            and isinstance(low_pass, dict | None)
        )

        return cls(
            volume,
            Equalizer.from_payloads_nullable(equalizers),
            Karaoke.from_payload_nullable(karaoke),
            Timescale.from_payload_nullable(timescale),
            Tremolo.from_payload_nullable(tremolo),
            Vibrato.from_payload_nullable(vibrato),
            Rotation.from_payload_nullable(rotation),
            Distortion.from_payload_nullable(distortion),
            ChannelMix.from_payload_nullable(channel_mix),
            LowPass.from_payload_nullable(low_pass),
        )

    def to_payload(self) -> PayloadType:
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
class Equalizer(BaseLavalinkModel):
    band: int
    gain: float

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        band = data["band"]
        gain = data["gain"]

        assert isinstance(band, int) and isinstance(gain, float)

        return cls(band, gain)


@attr.define()
class Karaoke(BaseLavalinkModel):
    level: float | None
    mono_level: float | None
    filter_band: float | None
    filter_width: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        level = data.get("level")
        mono_level = data.get("monoLevel")
        filter_band = data.get("filterBand")
        filter_width = data.get("filterWidth")

        assert (
            isinstance(level, float | None)
            and isinstance(mono_level, float | None)
            and isinstance(filter_band, float | None)
            and isinstance(filter_width, float | None)
        )

        return cls(level, mono_level, filter_band, filter_width)

    def to_payload(self) -> PayloadType:
        return {
            "level": self.level,
            "monoLevel": self.mono_level,
            "filterBand": self.filter_band,
            "filterWidth": self.filter_width,
        }


@attr.define()
class Timescale(BaseLavalinkModel):
    speed: float | None
    pitch: float | None
    rate: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        speed = data.get("speed")
        pitch = data.get("pitch")
        rate = data.get("rate")

        assert (
            isinstance(speed, float | None)
            and isinstance(pitch, float | None)
            and isinstance(rate, float | None)
        )

        return cls(speed, pitch, rate)


@attr.define()
class Tremolo(BaseLavalinkModel):
    frequency: float | None
    depth: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        frequency = data.get("frequency")
        depth = data.get("depth")

        assert isinstance(frequency, float | None) and isinstance(depth, float | None)

        return cls(frequency, depth)


@attr.define()
class Vibrato(BaseLavalinkModel):
    frequency: float | None
    depth: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        frequency = data.get("frequency")
        depth = data.get("depth")

        assert isinstance(frequency, float | None) and isinstance(depth, float | None)

        return cls(frequency, depth)


@attr.define()
class Rotation(BaseLavalinkModel):
    rotation_hz: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        rotation_hz = data.get("rotationHz")

        assert isinstance(rotation_hz, float | None)

        return cls(rotation_hz)

    def to_payload(self) -> PayloadType:
        return {"rotationHz": self.rotation_hz}


@attr.define()
class Distortion(BaseLavalinkModel):
    sin_offset: float | None
    sin_scale: float | None
    cos_offset: float | None
    cos_scale: float | None
    tan_offset: float | None
    tan_scale: float | None
    offset: float | None
    scale: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        sin_offset = data.get("sinOffset")
        sin_scale = data.get("sinScale")
        cos_offset = data.get("cosOffset")
        cos_scale = data.get("cosScale")
        tan_offset = data.get("tanOffset")
        tan_scale = data.get("tanScale")
        offset = data.get("offset")
        scale = data.get("scale")

        assert (
            isinstance(sin_offset, float | None)
            and isinstance(sin_scale, float | None)
            and isinstance(cos_offset, float | None)
            and isinstance(cos_scale, float | None)
            and isinstance(tan_offset, float | None)
            and isinstance(tan_scale, float | None)
            and isinstance(offset, float | None)
            and isinstance(scale, float | None)
        )

        return cls(
            sin_offset,
            sin_scale,
            cos_offset,
            cos_scale,
            tan_offset,
            tan_scale,
            offset,
            scale,
        )

    def to_payload(self) -> PayloadType:
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
class ChannelMix(BaseLavalinkModel):
    left_to_left: float | None
    left_to_right: float | None
    right_to_left: float | None
    right_to_right: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        left_to_left = data.get("leftToLeft")
        left_to_right = data.get("leftToRight")
        right_to_left = data.get("rightToLeft")
        right_to_right = data.get("rightToRight")

        assert (
            isinstance(left_to_left, float | None)
            and isinstance(left_to_right, float | None)
            and isinstance(right_to_left, float | None)
            and isinstance(right_to_right, float | None)
        )

        return cls(
            left_to_left,
            left_to_right,
            right_to_left,
            right_to_right,
        )

    def to_payload(self) -> PayloadType:
        return {
            "leftToLeft": self.left_to_left,
            "leftToRight": self.left_to_right,
            "rightToLeft": self.right_to_left,
            "rightToRight": self.right_to_right,
        }


@attr.define()
class LowPass(BaseLavalinkModel):
    smoothing: float | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        smoothing = data.get("smoothing")

        assert isinstance(smoothing, float | None)

        return cls(smoothing)


@attr.define()
class LoadTrackResult(BaseLavalinkModel):
    load_type: LoadResultType
    playlist_info: PlaylistInfo | None
    tracks: tuple[Track] | None
    exception: TrackException | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        load_type = data["loadType"]
        playlist_info = data["playlistInfo"]
        tracks = data["tracks"]
        exception = data.get("exception")

        assert (
            isinstance(load_type, str)
            and isinstance(playlist_info, dict)
            and isinstance(tracks, list)
            and is_payload_list(tracks)
            and isinstance(exception, dict | None)
        )

        return cls(
            LoadResultType(load_type),
            # `None` for empty results
            PlaylistInfo.from_payload(playlist_info) if playlist_info else None,
            Track.from_payloads(tracks) if tracks else None,
            TrackException.from_payload_nullable(exception),
        )


class LoadResultType(enum.Enum):
    TRACK_LOADED = "TRACK_LOADED"
    PLAYLIST_LOADED = "PLAYLIST_LOADED"
    SEARCH_RESULT = "SEARCH_RESULT"
    NO_MATCHES = "NO_MATCHES"
    LOAD_FAILED = "LOAD_FAILED"


@attr.define()
class PlaylistInfo(BaseLavalinkModel):
    name: str | None
    selected_track: int | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        name = data.get("name")
        selected_track = data.get("selectedTrack")

        assert isinstance(name, str | None) and isinstance(selected_track, int | None)

        return cls(name, selected_track)


@attr.define()
class LavalinkInfo(BaseLavalinkModel):
    version: Version
    build_time: datetime.datetime
    git: Git
    jvm: str
    lavaplayer: str
    source_managers: tuple[str]
    filters: tuple[str]
    plugins: tuple[Plugin]

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        version = data["version"]
        build_time = data["buildTime"]
        git = data["git"]
        jvm = data["jvm"]
        lavaplayer = data["lavaplayer"]
        source_managers = data["sourceManagers"]
        filters = data["filters"]
        plugins = data["plugins"]

        assert (
            isinstance(version, dict)
            and isinstance(build_time, int)
            and isinstance(git, dict)
            and isinstance(jvm, str)
            and isinstance(lavaplayer, str)
            and isinstance(source_managers, list)
            and is_str_list(source_managers)
            and isinstance(filters, list)
            and is_str_list(filters)
            and isinstance(plugins, list)
            and is_payload_list(plugins)
        )

        return cls(
            Version.from_payload(version),
            datetime.datetime.fromtimestamp(build_time / 1000),
            Git.from_payload(git),
            jvm,
            lavaplayer,
            (*source_managers,),
            (*filters,),
            Plugin.from_payloads(plugins),
        )


@attr.define()
class Version(BaseLavalinkModel):
    semver: str
    major: int
    minor: int
    patch: int
    pre_release: str | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        semver = data["semver"]
        major = data["major"]
        minor = data["minor"]
        patch = data["patch"]
        pre_release = data["preRelease"]

        assert (
            isinstance(semver, str)
            and isinstance(major, int)
            and isinstance(minor, int)
            and isinstance(patch, int)
            and isinstance(pre_release, str | None)
        )

        return cls(
            semver,
            major,
            minor,
            patch,
            pre_release,
        )


@attr.define()
class Git(BaseLavalinkModel):
    branch: str
    commit: str
    commit_time: datetime.datetime

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        branch = data["branch"]
        commit = data["commit"]
        commit_time = data["commitTime"]

        assert (
            isinstance(branch, str)
            and isinstance(commit, str)
            and isinstance(commit_time, int)
        )

        return cls(
            branch,
            commit,
            datetime.datetime.fromtimestamp(commit_time / 1000),
        )


@attr.define()
class Plugin(BaseLavalinkModel):
    name: str
    version: str

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        name = data["name"]
        version = data["version"]

        assert isinstance(name, str) and isinstance(version, str)

        return cls(name, version)


@attr.define()
class RoutePlannerStatus(BaseLavalinkModel):
    type: RoutePlannerType | None
    details: Details | None

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        type = data["type"]
        details = data["details"]

        assert isinstance(type, str | None) and isinstance(details, dict | None)

        return cls(
            RoutePlannerType(type) if type else None,
            Details.from_payload_nullable(details),
        )


class RoutePlannerType(enum.Enum):
    ROTATING_IP_ROUTE_PLANNER = "RotatingIpRoutePlanner"
    NANO_IP_ROUTE_PLANNER = "NanoIpRoutePlanner"
    ROTATING_NANO_IP_ROUTE_PLANNER = "RotatingNanoIpRoutePlanner"
    BALANCING_IP_ROUTE_PLANNER = "BalancingIpRoutePlanner"


@attr.define()
class Details(BaseLavalinkModel):
    ip_block: IPBlock
    failing_addresses: tuple[FailingAddress]
    rotate_index: str
    ip_index: str
    current_address: str
    current_address_index: str
    block_index: str

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        ip_block = data["ipBlock"]
        failing_addresses = data["failingAddresses"]
        rotate_index = data["rotateIndex"]
        ip_index = data["ipIndex"]
        current_address = data["currentAddress"]
        current_address_index = data["currentAddressIndex"]
        block_index = data["blockIndex"]

        assert (
            isinstance(ip_block, dict)
            and isinstance(failing_addresses, list)
            and is_payload_list(failing_addresses)
            and isinstance(rotate_index, str)
            and isinstance(ip_index, str)
            and isinstance(current_address, str)
            and isinstance(current_address_index, str)
            and isinstance(block_index, str)
        )

        return cls(
            IPBlock.from_payload(ip_block),
            FailingAddress.from_payloads(failing_addresses),
            rotate_index,
            ip_index,
            current_address,
            current_address_index,
            block_index,
        )


@attr.define()
class IPBlock(BaseLavalinkModel):
    type: IPBlockType
    size: str

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        type = data["type"]
        size = data["size"]

        assert isinstance(type, str) and isinstance(size, str)

        return cls(
            IPBlockType(type),
            size,
        )


class IPBlockType(enum.Enum):
    INET_4_ADDRESS = "Inet4Address"
    INET_6_ADDRESS = "Inet6Address"


@attr.define()
class FailingAddress(BaseLavalinkModel):
    address: str
    failing_time: datetime.datetime

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        address = data["address"]
        failing_time = data["failingTime"]

        assert isinstance(address, str) and isinstance(failing_time, int)

        return cls(
            address,
            datetime.datetime.fromtimestamp(failing_time / 1000),
        )
