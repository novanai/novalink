from __future__ import annotations

import abc
import datetime
import enum
import typing

import attr
import typing_extensions

import lavalink.types as types


class BaseLavalinkModel(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        ...

    @classmethod
    def from_payloads(
        cls, data: typing.Iterable[types.PayloadType]
    ) -> tuple[typing_extensions.Self, ...]:
        return tuple(cls.from_payload(d) for d in data)

    @typing.overload
    @classmethod
    def from_payload_nullable(cls, data: types.PayloadType) -> typing_extensions.Self:
        ...

    @typing.overload
    @classmethod
    def from_payload_nullable(cls, data: None) -> None:
        ...

    @classmethod
    def from_payload_nullable(
        cls, data: types.PayloadType | None
    ) -> typing_extensions.Self | None:
        return cls.from_payload(data) if data is not None else None

    @typing.overload
    @classmethod
    def from_payloads_nullable(
        cls, data: typing.Iterable[types.PayloadType]
    ) -> tuple[typing_extensions.Self, ...]:
        ...

    @typing.overload
    @classmethod
    def from_payloads_nullable(cls, data: None) -> None:
        ...

    @classmethod
    def from_payloads_nullable(
        cls, data: typing.Iterable[types.PayloadType] | None
    ) -> tuple[typing_extensions.Self, ...] | None:
        return tuple(cls.from_payload(d) for d in data) if data is not None else None


@attr.define()
class PlayerState(BaseLavalinkModel):
    """The player state."""
    time: datetime.datetime
    """Current UNIX time."""
    position: datetime.timedelta | None
    """Position of the track, if it is playing."""
    connected: bool
    """Whether lavalink is connected to the voice gateway."""
    ping: datetime.timedelta | None
    """The ping of the node to the Discord voice server. ``None`` if not connected."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """A collection of stats."""
    players: int
    """The amount of players connected to the node."""
    playing_players: int
    """The amount of players playing a track."""
    uptime: datetime.timedelta
    """The uptime of the node."""
    memory: Memory
    """The memory stats of the node."""
    cpu: CPU
    """The cpu stats of the node."""
    frame_stats: FrameStats | None
    """The frame stats of the node. ``None`` if the node has no players or when retrieved via
    :obj:`client.Lavalink.get_lavalink_stats`"""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """Memory stats."""
    free: int
    """The amount of free memory in bytes."""
    used: int
    """The amount of used memory in bytes."""
    allocated: int
    """The amount of allocated memory in bytes."""
    reservable: int
    """The amount of reservable memory in bytes."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """CPU stats."""
    cores: int
    """The amount of cores the node has."""
    system_load: float
    """The system load of the node."""
    lavalink_load: float
    """The load of lavalink on the node."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """Frames stats."""
    sent: int
    """The amount of frames sent to Discord."""
    nulled: int
    """The amount of frames that were nulled."""
    deficit: int
    """The amount of frames that were deficit."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """The track finished playing."""
    LOAD_FAILED = "LOAD_FAILED"
    """The track failed to load."""
    STOPPED = "STOPPED"
    """The track was stopped."""
    REPLACED = "REPLACED"
    """The track was replaced."""
    CLEANUP = "CLEANUP"
    """The track was cleaned up."""


class ExceptionSeverity(enum.Enum):
    COMMON = "COMMON"
    """The cause is known and expected, indicates that there is nothing wrong with lavalink itself."""
    SUSPICIOUS = "SUSPICIOUS"
    """The cause might not be exactly known, but is possibly caused by outside factors. For example when
    an outside service responds in a format that lavalink does not expect."""
    FATAL = "FATAL"
    """If the probable cause is an issue with lavalink or when there is no way to tell what the cause
    might be. This is the default level and other levels are used in cases where the thrower has more
    in-depth knowledge about the error."""


@attr.define()
class TrackException(BaseLavalinkModel):
    message: str | None
    """The message of the exception."""
    severity: ExceptionSeverity
    """The severity of the exception."""
    cause: str
    """The cause of the exception."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """A player."""
    guild_id: int
    """The guild ID of the player."""
    track: Track | None
    """The currently playing track."""
    volume: int
    """The volume of the player, range 0-1000, in percentage."""
    paused: bool
    """Whether the player is paused."""
    voice: VoiceState
    """The voice state of the player."""
    filters: Filters
    """The filters used by the player."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """A track."""
    encoded: str
    """The base64 encoded track data."""
    info: TrackInfo
    """Info about the track."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        encoded = data["encoded"]
        info = data["info"]

        assert isinstance(encoded, str) and isinstance(info, dict)

        return cls(encoded, TrackInfo.from_payload(info))


@attr.define()
class TrackInfo(BaseLavalinkModel):
    """Track info."""
    identifier: str
    """The track identifier."""
    is_seekable: bool
    """Whether the track is seekable."""
    author: str
    """The track author."""
    length: datetime.timedelta
    """The track length."""
    is_stream: bool
    """Whether the track is a stream."""
    position: datetime.timedelta
    """The track position."""
    title: str
    """The track title."""
    uri: str | None
    """The track uri."""
    source_name: str
    """The track source name."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """The Discord voice token to authenticate with."""
    endpoint: str
    """The Discord voice endpoint to connect to."""
    session_id: str
    """The Discord voice session id to authenticate with."""
    connected: bool | None = None
    """Whether the player is connected. Response only."""
    ping: int | None = None
    """Roundtrip latency in milliseconds to the voice gateway. ``None`` if not connected. Response only"""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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

    def to_payload(self) -> types.PayloadType:
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
    """Lets you adjust the player volume from 0.0 to 5.0 where 1.0 is 100%. Values >1.0 may cause clipping."""
    equalizers: tuple[Equalizer, ...] | None = None
    """Lets you adjust 15 different bands."""
    karaoke: Karaoke | None = None
    """Lets you eliminate part of a band, usually targeting vocals."""
    timescale: Timescale | None = None
    """Lets you change the speed, pitch, and rate."""
    tremolo: Tremolo | None = None
    """Lets you create a shuddering effect, where the volume quickly oscillates."""
    vibrato: Vibrato | None = None
    """Lets you create a shuddering effect, where the pitch quickly oscillates."""
    rotation: Rotation | None = None
    """Lets you rotate the sound around the stereo channels/user headphones aka Audio Panning."""
    distortion: Distortion | None = None
    """Lets you distort the audio."""
    channel_mix: ChannelMix | None = None
    """Lets you mix both channels (left and right)."""
    low_pass: LowPass | None = None
    """Lets you filter higher frequencies."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
            and types.is_payload_list_nullable(equalizers)
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

    def to_payload(self) -> types.PayloadType:
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
    """There are 15 bands (0-14) that can be changed. "gain" is the multiplier for the given band. The default value
    is 0. Valid values range from -0.25 to 1.0, where -0.25 means the given band is completely muted, and 0.25 means
    it is doubled. Modifying the gain could also change the volume of the output."""
    band: int
    """The band (0 to 14)."""
    gain: float
    """The gain (-0.25 to 1.0)."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        band = data["band"]
        gain = data["gain"]

        assert isinstance(band, int) and isinstance(gain, float)

        return cls(band, gain)


@attr.define()
class Karaoke(BaseLavalinkModel):
    level: float | None
    """The level (0 to 1.0 where 0.0 is no effect and 1.0 is full effect)."""
    mono_level: float | None
    """The mono level (0 to 1.0 where 0.0 is no effect and 1.0 is full effect)."""
    filter_band: float | None
    """The filter band."""
    filter_width: float | None
    """The filter width."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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

    def to_payload(self) -> types.PayloadType:
        return {
            "level": self.level,
            "monoLevel": self.mono_level,
            "filterBand": self.filter_band,
            "filterWidth": self.filter_width,
        }


@attr.define()
class Timescale(BaseLavalinkModel):
    """Changes the speed, pitch, and rate."""
    speed: float | None
    """The playback speed 0.0 ≤ x."""
    pitch: float | None
    """The pitch 0.0 ≤ x."""
    rate: float | None
    """The rate 0.0 ≤ x."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """Uses amplification to create a shuddering effect, where the volume quickly oscillates.
    https://en.wikipedia.org/wiki/File:Fuse_Electronics_Tremolo_MK-III_Quick_Demo.ogv"""
    frequency: float | None
    """The frequency 0.0 < x."""
    depth: float | None
    """The tremolo depth 0.0 < x ≤ 1.0."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        frequency = data.get("frequency")
        depth = data.get("depth")

        assert isinstance(frequency, float | None) and isinstance(depth, float | None)

        return cls(frequency, depth)


@attr.define()
class Vibrato(BaseLavalinkModel):
    """Similar to tremolo. While tremolo oscillates the volume, vibrato oscillates the pitch."""
    frequency: float | None
    """The frequency 0.0 < x ≤ 14.0."""
    depth: float | None
    """The vibrato depth 0.0 < x ≤ 1.0."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        frequency = data.get("frequency")
        depth = data.get("depth")

        assert isinstance(frequency, float | None) and isinstance(depth, float | None)

        return cls(frequency, depth)


@attr.define()
class Rotation(BaseLavalinkModel):
    """Rotates the sound around the stereo channels/user headphones aka Audio Panning."""
    rotation_hz: float | None
    """The frequency of the audio rotating around the listener in Hz."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        rotation_hz = data.get("rotationHz")

        assert isinstance(rotation_hz, float | None)

        return cls(rotation_hz)

    def to_payload(self) -> types.PayloadType:
        return {"rotationHz": self.rotation_hz}


@attr.define()
class Distortion(BaseLavalinkModel):
    """Distortion effect."""
    sin_offset: float | None
    """The sin offset."""
    sin_scale: float | None
    """The sin scale."""
    cos_offset: float | None
    """The cos offset."""
    cos_scale: float | None
    """The cos scale."""
    tan_offset: float | None
    """The tan offset."""
    tan_scale: float | None
    """The tan scale."""
    offset: float | None
    """The offset."""
    scale: float | None
    """The scale."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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

    def to_payload(self) -> types.PayloadType:
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
    """Mixes both channels (left and right), with a configurable factor on how much each channel affects the other.
    With the defaults, both channels are kept independent of each other. Setting all factors to 0.5 means both channels
    get the same audio."""
    left_to_left: float | None
    """The left to left channel mix factor (0.0 ≤ x ≤ 1.0)."""
    left_to_right: float | None
    """The left to right channel mix factor (0.0 ≤ x ≤ 1.0)."""
    right_to_left: float | None
    """The right to left channel mix factor (0.0 ≤ x ≤ 1.0)."""
    right_to_right: float | None
    """The right to right channel mix factor (0.0 ≤ x ≤ 1.0)."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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

    def to_payload(self) -> types.PayloadType:
        return {
            "leftToLeft": self.left_to_left,
            "leftToRight": self.left_to_right,
            "rightToLeft": self.right_to_left,
            "rightToRight": self.right_to_right,
        }


@attr.define()
class LowPass(BaseLavalinkModel):
    """Higher frequencies get suppressed, while lower frequencies pass through this filter, thus the name low pass.
    Any smoothing values equal to, or less than 1.0 will disable the filter."""
    smoothing: float | None
    """The smoothing factor (1.0 < x)."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        smoothing = data.get("smoothing")

        assert isinstance(smoothing, float | None)

        return cls(smoothing)


@attr.define()
class LoadTrackResult(BaseLavalinkModel):
    """Tracking loading result."""
    load_type: LoadResultType
    """The type of the result"""
    playlist_info: PlaylistInfo | None
    """Additional playlist info. Available for type :obj:`~LoadResultType.PLAYLIST_LOADED`."""
    tracks: tuple[Track, ...] | None
    """All tracks which have been loaded. Available for types :obj:`~LoadResultType.TRACK_LOADED`, 
    :obj:`~LoadResultType.PLAYLIST_LOADED` & :obj:`~LoadResultType.SEARCH_RESULT`."""
    exception: TrackException | None
    """The exception this load failed with. Available for type :obj:`~LoadResultType.LOAD_FAILED`."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        load_type = data["loadType"]
        playlist_info = data["playlistInfo"]
        tracks = data["tracks"]
        exception = data.get("exception")

        assert (
            isinstance(load_type, str)
            and isinstance(playlist_info, dict)
            and isinstance(tracks, list)
            and types.is_payload_list(tracks)
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
    """A track has been loaded."""
    PLAYLIST_LOADED = "PLAYLIST_LOADED"
    """A playlist has been loaded."""
    SEARCH_RESULT = "SEARCH_RESULT"
    """A search result has been loaded."""
    NO_MATCHES = "NO_MATCHES"
    """There has been no matches to your identifier."""
    LOAD_FAILED = "LOAD_FAILED"
    """Loading has failed."""


@attr.define()
class PlaylistInfo(BaseLavalinkModel):
    name: str | None
    """The name of the loaded playlist."""
    selected_track: int | None
    """The selected track in this Playlist. ``None`` if no track is selected."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        name = data.get("name")
        selected_track = data.get("selectedTrack")

        assert isinstance(name, str | None) and isinstance(selected_track, int | None)

        return cls(name, selected_track)


@attr.define()
class LavalinkInfo(BaseLavalinkModel):
    version: Version
    """The version of this Lavalink server."""
    build_time: datetime.datetime
    """The time when this Lavalink jar was built."""
    git: Git
    """The git information of this Lavalink server."""
    jvm: str
    """The JVM version this Lavalink server runs on."""
    lavaplayer: str
    """The Lavaplayer version being used by this server."""
    source_managers: tuple[str, ...]
    """The enabled source managers for this server."""
    filters: tuple[str, ...]
    """The enabled filters for this server."""
    plugins: tuple[Plugin, ...]
    """The enabled plugins for this server."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
            and types.is_str_list(source_managers)
            and isinstance(filters, list)
            and types.is_str_list(filters)
            and isinstance(plugins, list)
            and types.is_payload_list(plugins)
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
    """The full version string of this Lavalink server."""
    major: int
    """The major version of this Lavalink server."""
    minor: int
    """The minor version of this Lavalink server."""
    patch: int
    """The patch version of this Lavalink server."""
    pre_release: str | None
    """The pre-release version according to semver as a ``.`` separated list of identifiers. ``None`` if not a pre-release."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """The branch this Lavalink server was built."""
    commit: str
    """The commit this Lavalink server was built."""
    commit_time: datetime.datetime
    """The time when the commit was created."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
    """The name of the plugin."""
    version: str
    """The version of the plugin."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        name = data["name"]
        version = data["version"]

        assert isinstance(name, str) and isinstance(version, str)

        return cls(name, version)


@attr.define()
class RoutePlannerStatus(BaseLavalinkModel):
    type: RoutePlannerType | None
    """The type of the RoutePlanner implementation being used by this server."""
    details: Details | None
    """The status details of the RoutePlanner."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        type = data["type"]
        details = data["details"]

        assert isinstance(type, str | None) and isinstance(details, dict | None)

        return cls(
            RoutePlannerType(type) if type else None,
            Details.from_payload_nullable(details),
        )


class RoutePlannerType(enum.Enum):
    ROTATING_IP_ROUTE_PLANNER = "RotatingIpRoutePlanner"
    """IP address used is switched on ban. Recommended for IPv4 blocks or IPv6 blocks smaller than a /64."""
    NANO_IP_ROUTE_PLANNER = "NanoIpRoutePlanner"
    """IP address used is switched on clock update. Use with at least 1 /64 IPv6 block."""
    ROTATING_NANO_IP_ROUTE_PLANNER = "RotatingNanoIpRoutePlanner"
    """IP address used is switched on clock update, rotates to a different /64 block on ban. Use with at least 2x /64 IPv6 blocks."""
    BALANCING_IP_ROUTE_PLANNER = "BalancingIpRoutePlanner"
    """IP address used is selected at random per request. Recommended for larger IP blocks."""


@attr.define()
class Details(BaseLavalinkModel):
    ip_block: IPBlock
    """The ip block being used. Available for all of :obj:`~RoutePlannerType` types."""
    failing_addresses: tuple[FailingAddress, ...]
    """The failing addresses. Available for all of :obj:`~RoutePlannerType` types."""
    rotate_index: str
    """The number of rotations. Available for type :obj:`~RoutePlannerType.ROTATING_IP_ROUTE_PLANNER`."""
    ip_index: str
    """The current offset in the block. Available for type :obj:`~RoutePlannerType.ROTATING_IP_ROUTE_PLANNER`."""
    current_address: str
    """The current address being used. Available for type :obj:`~RoutePlannerType.ROTATING_IP_ROUTE_PLANNER`."""
    current_address_index: str
    """The current offset in the ip block. Available for types :obj:`~RoutePlannerType.ROTATING_IP_ROUTE_PLANNER`
    & :obj:`~RoutePlannerType.ROTATING_NANO_IP_ROUTE_PLANNER`."""
    block_index: str
    """The information in which /64 block ips are chosen. This number increases on each ban. Available for type
    :obj:`~RoutePlannerType.ROTATING_NANO_IP_ROUTE_PLANNER`."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
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
            and types.is_payload_list(failing_addresses)
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
    """The type of the ip block."""
    size: str
    """The size of the ip block."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        type = data["type"]
        size = data["size"]

        assert isinstance(type, str) and isinstance(size, str)

        return cls(
            IPBlockType(type),
            size,
        )


class IPBlockType(enum.Enum):
    INET_4_ADDRESS = "Inet4Address"
    """The ipv4 block type."""
    INET_6_ADDRESS = "Inet6Address"
    """The ipv6 block type."""


@attr.define()
class FailingAddress(BaseLavalinkModel):
    address: str
    """The failing address."""
    failing_time: datetime.datetime
    """The time when the address failed."""

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        address = data["address"]
        failing_time = data["failingTime"]

        assert isinstance(address, str) and isinstance(failing_time, int)

        return cls(
            address,
            datetime.datetime.fromtimestamp(failing_time / 1000),
        )
