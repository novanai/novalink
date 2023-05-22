from __future__ import annotations

import asyncio
import datetime
import json
import logging
import typing

import aiohttp

import lavalink.errors as errors
import lavalink.events as events
import lavalink.models as models
import lavalink.types as types
import lavalink.utils as utils

log = logging.getLogger(__name__)


class Lavalink:
    """A lavalink client.

    Parameters
    ----------
    host : str
        Host of the lavalink server.
    port : int
        Port of the lavalink server.
    is_secure : bool, default: False
        Whether the server is secure.
    heartbeat : int, default: 30
        How often to ping the lavalink server (in seconds).
    """

    def __init__(
        self,
        host: str,
        port: int,
        is_secure: bool = False,
        heartbeat: int = 30,  # or less?
    ) -> None:
        self.host = host
        self.port = port
        self.is_secure = is_secure
        self.heartbeat = heartbeat

        self._password: str | None = None
        self._bot_id: int | None = None
        self.resume_key: str | None = None
        self.shutdown: bool = False

        self._session_id: str | None = None
        self._session: aiohttp.ClientSession | None = None
        self._websocket: aiohttp.ClientWebSocketResponse | None = None

        self._voice_states: dict[int, models.VoiceState] = {}
        self._event_listeners: dict[
            type[events.Event], list[events.EventsCallbackT[events.Event]]
        ] = {}

    @property
    def password(self) -> str:
        """The password of the lavalink server passed to :obj:`~Lavalink.start()`."""
        if self._password is None:
            raise RuntimeError("password is None, Lavalink.start() was never called.")

        return self._password

    @property
    def bot_id(self) -> int:
        """The user ID of the bot passed to :obj:`~Lavalink.start()`."""
        if not self._bot_id:
            raise RuntimeError("bot_id is None, Lavalink.start() was never called")

        return self._bot_id

    @property
    def session_id(self) -> str:
        """The lavalink session ID."""
        if self._session_id is None:
            raise RuntimeError("session_id is None, Lavalink.start() was never called.")

        return self._session_id

    @property
    def session(self) -> aiohttp.ClientSession:
        """A :obj:`~aiohttp.ClientSession` for making requests to the lavalink server."""
        if not self._session:
            raise RuntimeError("session is None, Lavalink.start() was never called")

        return self._session

    @property
    def websocket(self) -> aiohttp.ClientWebSocketResponse:
        """A websocket connection with the lavalink server."""
        if not self._websocket:
            raise RuntimeError("Not connected to websocket")

        return self._websocket

    @property
    def voice_states(self) -> dict[int, models.VoiceState]:
        """A mapping of guild ID to the bot's :obj:`~lavalink.models.VoiceState`"""
        return self._voice_states

    async def start(
        self,
        password: str,
        bot_id: int,
        resume_key: str | None = None,
    ) -> None:
        """Connect to the lavalink websocket and start listening for events.

        Parameters
        ----------
        password : str
            The password of the lavalink server, set in the
            `lavalink config <https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example>`_.
        bot_id : int
            The user ID of the bot.
        resume_key : str, optional
            A resume key, used to resume a session.
        """
        self._password = password
        self._bot_id = bot_id
        self._resume_key = resume_key

        headers = {
            "Authorization": password,
            "User-Id": str(bot_id),
            "Client-Name": "lava.py/0.0.0",
        }
        if resume_key:
            headers["Resume-Key"] = resume_key

        self._session = aiohttp.ClientSession(
            headers=headers,
        )

        await self._connect()
        asyncio.create_task(self._receive())

    async def stop(self) -> None:
        """Stop listening for events and close the websocket connection."""
        self.shutdown = True
        await self.session.close()
        await self.websocket.close()

    async def _connect(self) -> None:
        while not self._websocket:
            try:
                self._websocket = await self.session.ws_connect(  # pyright: ignore[reportUnknownMemberType]
                    f"{'wss' if self.is_secure else 'ws'}://{self.host}:{self.port}/v3/websocket",
                    heartbeat=self.heartbeat,
                )
            except (aiohttp.ClientConnectorError, aiohttp.WSServerHandshakeError) as e:
                log.error(f"Couldn't connect to websocket, retrying in 5 seconds ({e})")

            await asyncio.sleep(5)

        log.info("Connected to websocket")

    async def _receive(self) -> None:
        while not self.shutdown:
            msg = await self.websocket.receive()
            if (
                msg.type  # pyright: ignore[reportUnknownMemberType]
                == aiohttp.WSMsgType.CLOSED
            ):
                log.error("websocket closed, reconnecting...")
                self._websocket = None
                await self._connect()

            elif (
                msg.type  # pyright: ignore[reportUnknownMemberType]
                == aiohttp.WSMsgType.TEXT
            ):
                asyncio.create_task(
                    self._handle_payload(
                        msg.data  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                    )
                )

    async def _handle_payload(self, data_str: str) -> None:
        data: types.PayloadType = json.loads(data_str)
        op = data["op"]

        if op == "ready":
            session_id = data["sessionId"]
            assert isinstance(session_id, str)
            self._session_id = session_id

            if self.resume_key:
                await self.update_session(self.resume_key)

            self.dispatch(events.ReadyEvent, data)

        elif op == "playerUpdate":
            self.dispatch(events.PlayerUpdateEvent, data)

        elif op == "stats":
            self.dispatch(events.StatsEvent, data)

        elif op == "event":
            type = data["type"]
            if type == "TrackStartEvent":
                self.dispatch(events.TrackStartEvent, data)
            elif type == "TrackEndEvent":
                self.dispatch(events.TrackEndEvent, data)
            elif type == "TrackExceptionEvent":
                self.dispatch(events.TrackExceptionEvent, data)
            elif type == "TrackStuckEvent":
                self.dispatch(events.TrackStuckEvent, data)
            elif type == "WebSocketClosedEvent":
                self.dispatch(events.WebSocketClosedEvent, data)

    def dispatch(self, event_type: type[events.Event], data: types.PayloadType) -> None:
        if listeners := self._event_listeners.get(event_type):
            event = event_type.from_payload(data)
            for listener in listeners:
                asyncio.create_task(listener(event))

    @typing.overload
    def listen(
        self,
        event_type: type[typing.Any],
    ) -> typing.Callable[[events.EventsCallbackT[typing.Any]], None]:
        ...

    @typing.overload
    def listen(
        self,
        event_type: type[typing.Any],
        callback: events.EventsCallbackT[typing.Any],
    ) -> None:
        ...

    def listen(
        self,
        event_type: type[typing.Any],
        callback: events.EventsCallbackT[typing.Any] | None = None,
    ) -> typing.Callable[[events.EventsCallbackT[typing.Any]], None] | None:
        """Listen for an event received from the lavalink server.

        Parameters
        ----------
            event_type : subclass of :obj:`~lavalink.events.Event`
                The event to listen for.
            callback : events.EventsCallbackT[typing.Any], optional
                The callback function for this event, if not used as a decorator

        Example
        -------
        .. code-block:: python

            lava = lavalink.Lavalink(...)

            @lava.listen(lavalink.ReadyEvent)
            async def on_ready(event: lavalink.ReadyEvent):
                print(f"Lavalink is ready! Session ID: {event.session_id}")

            # OR

            async def on_ready(event: lavalink.ReadyEvent):
                print(f"Lavalink is ready! Session ID: {event.session_id}")

            lava.listen(lavalink.ReadyEvent, on_ready)
        """
        if callback:
            self._add_event_listener(event_type, callback)
            return None

        def decorator(
            callback: events.EventsCallbackT[typing.Any],
        ) -> None:
            self._add_event_listener(event_type, callback)

        return decorator

    def _add_event_listener(
        self,
        event_type: type[typing.Any],
        callback: events.EventsCallbackT[typing.Any],
    ) -> None:
        if event_type in self._event_listeners:
            self._event_listeners[event_type].append(callback)
        else:
            self._event_listeners[event_type] = [callback]

    def handle_voice_server_update(
        self, guild_id: int, endpoint: str | None, token: str
    ) -> None:
        """Handle a voice server update event sent by Discord.

        Parameters
        ----------
        guild_id : int
            The ID of the guild this event happened in.
        endpoint : str | None
            The endpoint provided by Discord.
        token : str
            The token provided by Discord.
        """
        if self._voice_states.get(guild_id):
            if endpoint:
                self._voice_states[guild_id].endpoint = endpoint.replace("wss://", "")
                asyncio.create_task(
                    self.update_player(guild_id, voice=self._voice_states[guild_id])
                )

            self._voice_states[guild_id].token = token

    def handle_voice_state_update(
        self, guild_id: int, user_id: int, session_id: str
    ) -> None:
        """Handle a voice state update event sent by Discord.

        Parameters
        ----------
        guild_id : int
            The ID of the guild this event happened in.
        user_id : int
            The ID of the user this event regards.
        session_id : str
            The session ID provided by Discord.
        """
        if user_id != self.bot_id:
            return

        if self._voice_states.get(guild_id):
            self._voice_states[guild_id].session_id = session_id

        else:
            self._voice_states[guild_id] = models.VoiceState(
                "", "", session_id, None, None
            )

    # REST API METHODS

    async def request(
        self,
        method: typing.Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        *,
        params: types.MutablePayloadType | None = None,
        data: types.PartiallyUndefinablePayloadType | list[str] | None = None,
    ) -> typing.Any:
        if not params:
            params = {}
        params["trace"] = "true"

        async with self.session.request(
            method,
            f"{'https' if self.is_secure else 'http'}://{self.host}:{self.port}/{path}",
            params=params,
            json=data,
        ) as res:
            if res.content_type == "application/json":
                rdata = await res.json()

                if not res.ok:
                    raise errors.LavalinkError.from_payload(rdata)

                return rdata

            if not res.ok:
                res.raise_for_status()

            if res.content_type == "text/plain":
                return (await res.read()).decode("utf-8")

    async def get_players(self) -> list[models.Player]:
        """Get a list of players for this session."""
        return [
            models.Player.from_payload(p)
            for p in await self.request("GET", f"v3/sessions/{self.session_id}/players")
        ]

    async def get_player(self, guild_id: int) -> models.Player:
        """Get the player for a specific guild in this session.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get a player for.
        """
        return models.Player.from_payload(
            await self.request(
                "GET", f"v3/sessions/{self.session_id}/players/{guild_id}"
            )
        )

    async def update_player(
        self,
        guild_id: int,
        *,
        no_replace: types.UndefinedOr[bool] = types.UNDEFINED,
        encoded_track: types.UndefinedOr[str | None] = types.UNDEFINED,
        identifier: types.UndefinedOr[str] = types.UNDEFINED,
        position: types.UndefinedOr[datetime.timedelta] = types.UNDEFINED,
        end_time: types.UndefinedOr[datetime.timedelta] | None = types.UNDEFINED,
        volume: types.UndefinedOr[int] = types.UNDEFINED,
        paused: types.UndefinedOr[bool] = types.UNDEFINED,
        filters: types.UndefinedOr[models.Filters] = types.UNDEFINED,
        voice: types.UndefinedOr[models.VoiceState] = types.UNDEFINED,
    ) -> models.Player:
        """Update or create a player for the specified guild in this session.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to update or create the player for.
        no_replace : bool, default: False
            Whether to replace the current track with the new track.
        encoded_track : str | None, optional
            The base64 encoded track to play. ``None`` stops the current track.
        identifier : str, optional
            The identifier of the track to play.

            .. note::

                ``encoded_rack`` and ``identifier`` are mutually exclusive.

        position : datetime.timedelta, optional
            The track position.
        end_time : datetime.timedelta | None, optional
            The track end time. Must be > 0.
        volume : int, optional
            The player volume from 0 to 1000.
        paused : bool, optional
            Whether the player is paused.
        filters : models.Filters, optional
            The new filters to apply. This will override all previously applied filters.
        voice : models.VoiceState, optional
            Information required for connecting to Discord.
        """
        if (encoded_track or identifier) and not self.voice_states.get(guild_id):
            raise ValueError(
                "Can't play track without voice state information. Did you forget to join a channel?"
            )

        query = f"v3/sessions/{self.session_id}/players/{guild_id}"
        params: types.MutablePayloadType = {"noReplace": "true"} if no_replace else {}

        if voice:
            voice_dict = typing.cast(types.MutablePayloadType, voice.to_payload())
            voice_dict.pop("connected")
            voice_dict.pop("ping")
        else:
            voice_dict = types.UNDEFINED


        def to_ms(x: datetime.timedelta) -> float:
            return x.total_seconds() * 1000

        data = {
            "encodedTrack": encoded_track,
            "identifier": identifier,
            "position": utils.and_then(position, to_ms),
            "endTime": utils.and_then(end_time, to_ms) if end_time is not None else end_time,
            "volume": volume,
            "paused": paused,
            "filters": utils.and_then(filters, lambda f: f.to_payload()),
            "voice": voice_dict,
        }
        data = utils.remove_undefined_values(data)

        return models.Player.from_payload(
            await self.request("PATCH", query, params=params, data=data)
        )

    async def destroy_player(self, guild_id: int) -> None:
        """Destroys the player for the specified guild in this session.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to destroy the player for.
        """
        await self.request(
            "DELETE",
            f"v3/sessions/{self.session_id}/players/{guild_id}",
        )

    async def update_session(
        self,
        resuming_key: types.UndefinedOr[str | None] = types.UNDEFINED,
        timeout: types.UndefinedOr[int] = types.UNDEFINED,
    ) -> None:
        """Update this session with a resuming key and timeout.

        Parameters
        ----------
        resuming_key : str, optional
            The resuming key to be able to resume this session later.
        timeout: int, default: 60
            The timeout in seconds.
        """
        await self.request(
            "PATCH",
            f"v3/sessions/{self.session_id}",
            data=utils.remove_undefined_values(
                {
                    "resumingKey": resuming_key,
                    "timeout": timeout,
                }
            ),
        )

    async def load_track(self, identifier: str) -> models.LoadTrackResult:
        """Load a track.

        Parameters
        ----------
        identifier : str
            The track's identifier.
        """
        return models.LoadTrackResult.from_payload(
            await self.request(
                "GET", "v3/loadtracks", params={"identifier": identifier}
            )
        )

    async def decode_track(self, encoded: str) -> models.Track:
        """Decode a base64 encoded track into its info.

        Parameters
        ----------
        encoded : str
            The encoded track.
        """
        return models.Track.from_payload(
            await self.request(
                "GET",
                "v3/decodetrack",
                params={
                    "encodedTrack": encoded,
                },
            )
        )

    async def decode_tracks(self, encoded: list[str]) -> list[models.Track]:
        """Decode multiple base64 encoded tracks into their info.

        Parameters
        ----------
        encoded : list[str]
            The encoded tracks.
        """
        return [
            models.Track.from_payload(t)
            for t in await self.request("GET", "v3/decodetracks", data=encoded)
        ]

    async def get_lavalink_info(self) -> models.LavalinkInfo:
        """Get the lavalink server information."""
        return models.LavalinkInfo.from_payload(
            await self.request(
                "GET",
                "v3/info",
            )
        )

    async def get_lavalink_stats(self) -> models.Stats:
        """Get the lavalink server stats."""
        return models.Stats.from_payload(
            await self.request(
                "GET",
                "v3/stats",
            )
        )

    async def get_lavalink_version(self) -> str:
        """Get the lavalink version."""
        return await self.request("GET", "version")

    async def get_routeplanner_status(self) -> models.RoutePlannerStatus:
        """Get the RoutePlanner status."""
        return models.RoutePlannerStatus.from_payload(
            await self.request("GET", "v3/routeplanner/status")
        )

    async def unmark_failed_address(self, address: str) -> None:
        """Unmark a failed address.

        Parameters
        ----------
        address : str
            The address to unmark.
        """
        await self.request(
            "POST", "v3/routeplanner/free/address", data={"address": address}
        )

    async def unmark_all_failed_addresses(self) -> None:
        """Unmark all failed addresses."""
        await self.request(
            "POST",
            "v3/routeplanner/free/all",
        )
