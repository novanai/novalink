from __future__ import annotations

import asyncio
import json
import logging
import typing

import aiohttp

import lava.types as types, lava.errors as errors, lava.events as events, lava.models as models, lava.utils as utils


log = logging.getLogger(__name__)


class Lavalink:
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

        self.voice_states: dict[int, models.VoiceState] = {}
        self.event_listeners: dict[
            type[events.Event], list[events.EventsCallbackT[events.Event]]
        ] = {}

    @property
    def password(self) -> str:
        if self._password is None:
            raise RuntimeError("password is None, Lavalink.connect() was never called.")

        return self._password

    @property
    def bot_id(self) -> int:
        if not self._bot_id:
            raise RuntimeError("bot_id is None, Lavalink.connect() was never called")

        return self._bot_id

    @property
    def session_id(self) -> str:
        if self._session_id is None:
            raise RuntimeError(
                "session_id is None, Lavalink.connect() was never called."
            )

        return self._session_id

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("session is None, Lavalink.connect() was never called")

        return self._session

    @property
    def websocket(self) -> aiohttp.ClientWebSocketResponse:

        if not self._websocket:
            raise RuntimeError("Not connected to websocket")

        return self._websocket

    async def start(
        self,
        password: str,
        bot_id: int,
        resume_key: str | None = None,
    ) -> None:
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
        asyncio.create_task(self.receive())

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

    async def stop(self) -> None:
        self.shutdown = True
        await self.session.close()
        await self.websocket.close()

    async def receive(self) -> None:
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

        if data["op"] == "ready":
            session_id = data["sessionId"]
            assert isinstance(session_id, str)
            self._session_id = session_id

            if self.resume_key:
                await self.update_session(self.resume_key)

            self.dispatch(events.ReadyEvent, data)

        elif data["op"] == "playerUpdate":
            self.dispatch(events.PlayerUpdateEvent, data)

        elif data["op"] == "stats":
            self.dispatch(events.StatsEvent, data)

        elif data["op"] == "event":
            if data["type"] == "TrackStartEvent":
                self.dispatch(events.TrackStartEvent, data)
            elif data["type"] == "TrackEndEvent":
                self.dispatch(events.TrackEndEvent, data)
            elif data["type"] == "TrackExceptionEvent":
                self.dispatch(events.TrackExceptionEvent, data)
            elif data["type"] == "TrackStuckEvent":
                self.dispatch(events.TrackStuckEvent, data)
            elif data["type"] == "WebSocketClosedEvent":
                self.dispatch(events.WebSocketClosedEvent, data)

    def dispatch(self, event_type: type[events.Event], data: types.PayloadType) -> None:
        if listeners := self.event_listeners.get(event_type):
            event = event_type.from_payload(data)
            for listener in listeners:
                asyncio.create_task(listener(event))

    def listen(
        self, event_type: type[typing.Any]
    ) -> typing.Callable[[events.EventsCallbackT[typing.Any]], None]:
        def decorator(
            callback: events.EventsCallbackT[typing.Any],
        ) -> None:
            if event_type in self.event_listeners:
                self.event_listeners[event_type].append(callback)
            else:
                self.event_listeners[event_type] = [callback]

        return decorator

    def handle_voice_server_update(
        self, guild_id: int, endpoint: str | None, token: str
    ) -> None:
        # TODO: Handle endpoint = None disconnect, but how?
        if self.voice_states.get(guild_id):
            if endpoint:
                self.voice_states[guild_id].endpoint = endpoint.replace("wss://", "")
            self.voice_states[guild_id].token = token
            # discord should send a new endpoint later

    def handle_voice_state_update(
        self, guild_id: int, user_id: int, session_id: str
    ) -> None:
        if user_id != self.bot_id:
            return

        if self.voice_states.get(guild_id):
            self.voice_states[guild_id].session_id = session_id

        else:
            self.voice_states[guild_id] = models.VoiceState(
                "", "", session_id, None, None
            )

    # REST API METHODS

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: types.MutablePayloadType | None = None,
        data: types.PartiallyNullablePayloadType | list[str] | None = None,
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
        return [
            models.Player.from_payload(p)
            for p in await self.request("GET", f"v3/sessions/{self.session_id}/players")
        ]

    async def get_player(self, guild_id: int) -> models.Player:
        return models.Player.from_payload(
            await self.request(
                "GET", f"v3/sessions/{self.session_id}/players/{guild_id}"
            )
        )

    async def update_player(
        self,
        guild_id: int,
        no_replace: bool | None = None,
        encoded_track: str | None = None,
        identifier: str | None = None,
        position: int | None = None,
        end_time: int | None = None,
        volume: int | None = None,
        paused: bool | None = None,
        filters: models.Filters | None = None,
        voice: models.VoiceState | None = None,
    ) -> models.Player:
        query = f"v3/sessions/{self.session_id}/players/{guild_id}"
        params: types.MutablePayloadType = {"noReplace": "true"} if no_replace else {}

        if voice:
            voice_dict = typing.cast(
                types.MutableNullablePayloadType, voice.to_payload()
            )
            voice_dict.pop("connected")
            voice_dict.pop("ping")
        else:
            voice_dict = None

        data = {
            "encodedTrack": encoded_track,
            "identifier": identifier,
            "position": position,
            "endTime": end_time,
            "volume": volume,
            "paused": paused,
            "filters": filters.to_payload() if filters else None,
            "voice": voice_dict,
        }
        data = utils.remove_null_values(data)

        return models.Player.from_payload(
            await self.request("PATCH", query, params=params, data=data)
        )

    async def destroy_player(self, guild_id: int) -> None:
        await self.request(
            "DELETE",
            f"v3/sessions/{self.session_id}/players/{guild_id}",
        )

    async def update_session(
        self, resuming_key: str | None = None, timeout: int | None = None
    ) -> None:
        # TODO: Add return value?
        await self.request(
            "PATCH",
            f"v3/sessions/{self.session_id}",
            data=utils.remove_null_values(
                {
                    "resumingKey": resuming_key,
                    "timeout": timeout,
                }
            ),
        )

    async def load_track(self, identifier: str) -> models.LoadTrackResult:
        return models.LoadTrackResult.from_payload(
            await self.request(
                "GET", "v3/loadtracks", params={"identifier": identifier}
            )
        )

    async def decode_track(self, encoded: str) -> models.Track:
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
        return [
            models.Track.from_payload(t)
            for t in await self.request("GET", "v3/decodetracks", data=encoded)
        ]

    async def get_lavalink_info(self) -> models.LavalinkInfo:
        return models.LavalinkInfo.from_payload(
            await self.request(
                "GET",
                "v3/info",
            )
        )

    async def get_lavalink_stats(self) -> models.Stats:
        return models.Stats.from_payload(
            await self.request(
                "GET",
                "v3/stats",
            )
        )

    async def get_lavalink_version(self) -> str:
        return await self.request("GET", "version")

    async def get_routeplanner_status(self) -> models.RoutePlannerStatus:
        return models.RoutePlannerStatus.from_payload(
            await self.request("GET", "v3/routeplanner/status")
        )

    async def unmark_failed_address(self, address: str) -> None:
        await self.request(
            "POST", "v3/routeplanner/free/address", data={"address": address}
        )

    async def unmark_all_failed_addresses(self) -> None:
        await self.request(
            "POST",
            "v3/routeplanner/free/all",
        )
