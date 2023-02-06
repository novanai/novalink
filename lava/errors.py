from __future__ import annotations

import datetime

import attr


@attr.define()
class LavalinkError(Exception):
    timestamp: datetime.datetime
    status: int
    error: str
    trace: str | None
    message: str
    path: str

    def __str__(self) -> str:
        return f"{self.status} {self.error} for '{self.path}'. Message: {self.message}"

    @classmethod
    def from_payload(cls, data: dict) -> LavalinkError:
        return cls(
            datetime.datetime.fromtimestamp(data["timestamp"] / 1000),
            data["status"],
            data["error"],
            data.get("trace"),
            data["message"],
            data["path"],
        )
