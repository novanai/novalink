from __future__ import annotations

import datetime

import attr
import typing_extensions

import lavalink.models as models
import lavalink.types as types


@attr.define()
class LavalinkError(models.BaseLavalinkModel, Exception):
    """An error returned by the lavalink server."""

    time: datetime.datetime
    """The time the error occurred."""
    status: int
    """The HTTP status code."""
    error: str
    """The HTTP status code message."""
    trace: str | None
    """The stack trace of the error."""
    message: str
    """The error message."""
    path: str
    """The request path."""

    def __str__(self) -> str:
        return f"{self.status} {self.error} for '{self.path}'. Message: {self.message}"

    @classmethod
    def from_payload(cls, data: types.PayloadType) -> typing_extensions.Self:
        timestamp = data["timestamp"]
        status = data["status"]
        error = data["error"]
        trace = data.get("trace")
        message = data["message"]
        path = data["path"]

        assert (
            isinstance(timestamp, int)
            and isinstance(status, int)
            and isinstance(error, str)
            and isinstance(trace, str | None)
            and isinstance(message, str)
            and isinstance(path, str)
        )

        return cls(
            datetime.datetime.fromtimestamp(timestamp / 1000),
            status,
            error,
            trace,
            message,
            path,
        )
