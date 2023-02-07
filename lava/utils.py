import typing
import typing_extensions
import urllib.parse as parse

from .types import PayloadType


class LavalinkObject(typing.Protocol):
    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        ...


_ClassT = typing.TypeVar('_ClassT', bound=LavalinkObject)


def remove_null_values(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


def from_nullable_payload(
    cls: type[_ClassT], data: PayloadType | None
) -> _ClassT | None:
    return cls.from_payload(data) if data is not None else None


def from_nullable_payloads(
    cls: type[_ClassT], data: list[PayloadType] | None
) -> tuple[_ClassT] | None:
    return tuple(cls.from_payload(d) for d in data) if data is not None else None
