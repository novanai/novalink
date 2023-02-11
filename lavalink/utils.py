import typing

import typing_extensions

from .types import PayloadType


class LavalinkObject(typing.Protocol):
    @classmethod
    def from_payload(cls, data: PayloadType) -> typing_extensions.Self:
        ...


def remove_null_values(**kwargs: PayloadType) -> PayloadType:
    return {k: v for k, v in kwargs.items() if v is not None}
