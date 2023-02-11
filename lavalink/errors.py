from __future__ import annotations

import datetime

import attr
import typing_extensions

from .models import BaseLavalinkModel
from .types import PayloadType


@attr.define()
class LavalinkError(BaseLavalinkModel, Exception):
    timestamp: datetime.datetime
    status: int
    error: str
    trace: str | None
    message: str
    path: str

    def __str__(self) -> str:
        return f"{self.status} {self.error} for '{self.path}'. Message: {self.message}"

    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
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
