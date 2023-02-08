from __future__ import annotations

import asyncio
import json
import logging
import typing

import aiohttp

import errors, events, models, utils

log = logging.getLogger(__name__)


class Lavalink:
    def __init__(self) -> None:
        self._is_ssl: bool | None = None
        self._host: str | None = None
        self._port: int | str | None = None
        self._bot_id: int | None = None

        self._session_id: str | None = None

        self.voice_states: dict[int, models.VoiceState] = {}

        self._session: aiohttp.ClientSession | None = None
        self._websocket: aiohttp.client._WSRequestContextManager | None = (  # pyright: ignore [reportPrivateUsage]
            None
        )

        self.event_listeners: dict[
            typing.Type[events.Event], list[events.EventsCallbackT]
        ] = {}

    @property
    def is_ssl(self) -> bool:
        if self._is_ssl is None:
            raise RuntimeError("Lavalink.connect() was not called.")

        return self._is_ssl

    @property
    def host(self) -> str:
        if self._host is None:
            raise RuntimeError("host Lavalink.connect() was not called.")

        return self._host

    @property
    def port(self) -> int | str:
        if self._port is None:
            raise RuntimeError("port Lavalink.connect() was not called.")

        return self._port

    @property
    def bot_id(self) -> int | str:
        if self._bot_id is None:
            raise RuntimeError("bot_id Lavalink.connect() was not called.")

        return self._bot_id

    @property
    def session_id(self) -> str:
        if self._session_id is None:
            raise RuntimeError("session_id Lavalink.connect() was not called.")

        return self._session_id

    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("session Lavalink.connect() was not called.")

        return self._session

    @property
    def websocket(self) -> aiohttp.client._WSRequestContextManager:
        if not self._websocket:
            raise RuntimeError("websocket Lavalink.connect() was not called.")

        return self._websocket

    async def close(self) -> None:
        await self.session.close()
        self.websocket.close()

    async def connect(
        self,
        host: str,
        port: int | str,
        password: str,
        bot_id: int,
        resume_key: str | None = None,
        is_ssl: bool = False,
    ) -> None:
        self._is_ssl = is_ssl
        self._host = host
        self._port = port
        self._bot_id = bot_id

        headers = {
            "Authorization": password,
            "User-Id": str(bot_id),
            "Client-Name": "lava.py/0.0.0",
        }
        if resume_key:
            headers["Resume-Key"] = resume_key

        self._session = aiohttp.ClientSession(headers=headers)
        self._websocket = self._session.ws_connect(
            f"{'wss' if is_ssl else 'ws'}://{host}:{port}/v3/websocket"
        )

        asyncio.create_task(self._start_listening())

    async def _start_listening(self) -> None:
        async with self.websocket as ws:
            async for msg in ws:
                data: dict = json.loads(msg.data)

                if data["op"] == "ready":
                    self._session_id = data["sessionId"]
                    self.dispatch(events.ReadyEvent.from_payload(data))

                elif data["op"] == "playerUpdate":
                    self.dispatch(events.PlayerUpdateEvent.from_payload(data))

                elif data["op"] == "stats":
                    self.dispatch(
                        events.StatsEvent.from_payload(data)  # what's up here?
                    )

                elif data["op"] == "event":
                    if data["type"] == "TrackStartEvent":
                        self.dispatch(events.TrackStartEvent.from_payload(data))
                    elif data["type"] == "TrackEndEvent":
                        self.dispatch(events.TrackEndEvent.from_payload(data))
                    elif data["type"] == "TrackExceptionEvent":
                        self.dispatch(events.TrackExceptionEvent.from_payload(data))
                    elif data["type"] == "TrackStuckEvent":
                        self.dispatch(events.TrackStuckEvent.from_payload(data))
                    elif data["type"] == "WebSocketClosedEvent":
                        self.dispatch(events.WebSocketClosedEvent.from_payload(data))

    def dispatch(self, event: events.Event) -> None:
        if listeners := self.event_listeners.get(type(event)):
            for listener in listeners:
                asyncio.create_task(listener(event))  # type: ignore[arg-type]

    def listen(
        self, event_type: typing.Type[events.EventT]
    ) -> typing.Callable[[events.EventsCallbackT], None]:
        def decorator(
            callback: events.EventsCallbackT,
        ) -> None:
            if event_type in self.event_listeners:
                self.event_listeners[event_type].append(callback)
            else:
                self.event_listeners[event_type] = [callback]

        return decorator

    def handle_voice_server_update(
        self, guild_id: int, endpoint: str | None, token: str
    ) -> None:
        # TODO: Handle endpoint = None disconnect
        if self.voice_states.get(guild_id):
            if endpoint:
                self.voice_states[guild_id].endpoint = endpoint.replace("wss://", "")
            self.voice_states[guild_id].token = token

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
        self, method: str, path: str, params: dict = {}, data: dict | list | None = None
    ) -> typing.Any:
        params["trace"] = "true"

        async with self.session.request(
            method,
            f"{'https' if self.is_ssl else 'http'}://{self.host}:{self.port}/{path}",
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
        params = {"noReplace": "true"} if no_replace else {}

        if voice:
            voice_dict = voice.to_payload()
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
        data = utils.remove_null_values(**data)

        return models.Player.from_payload(
            await self.request("PATCH", query, params, data)
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
                resumingKey=resuming_key,
                timeout=timeout,
            ),
        )

    async def load_track(self, identifier: str) -> models.LoadTrackResult:
        return models.LoadTrackResult.from_payload(
            await self.request("GET", "v3/loadtracks", {"identifier": identifier})
        )

    async def decode_track(self, encoded: str) -> models.Track:
        return models.Track.from_payload(
            await self.request(
                "GET",
                "v3/decodetrack",
                {
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
