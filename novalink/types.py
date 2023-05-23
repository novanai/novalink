import typing

import attr


@attr.define(hash=True, init=False, frozen=True)
class UndefinedType(object):
    def __bool__(self) -> typing.Literal[False]:
        return False


_T_co = typing.TypeVar("_T_co", bound=typing.Any, covariant=True)
UNDEFINED = UndefinedType()
"""A sentinel singleton that denotes a missing or omitted value when making api requests."""
UndefinedOr = _T_co | UndefinedType
"""Type hint to mark a type as being semantically optional.

.. note::

    ``UndefinedOr[str]`` means ``str`` or ``UNDEFINED``, **not** ``None``
"""

_T = typing.TypeVar("_T")
MaybeSequence = _T | typing.Sequence[_T]
AwaitableNull = typing.Coroutine[typing.Any, typing.Any, None]

AtomicTypes = str | int | float | bool | None
UndefinableAtomicTypes = AtomicTypes | UndefinedType

PayloadValueTypes = MaybeSequence[AtomicTypes] | MaybeSequence["PayloadType"]
PartiallyUndefinablePayloadValueTypes = (
    UndefinableAtomicTypes | typing.Sequence[AtomicTypes] | MaybeSequence["PayloadType"]
)

PayloadType = typing.Mapping[str, PayloadValueTypes]
PartiallyUndefinablePayloadType = typing.Mapping[
    str, PartiallyUndefinablePayloadValueTypes
]
MutablePayloadType = typing.MutableMapping[str, PayloadValueTypes]
MutablePartiallyUndefinablePayloadType = typing.MutableMapping[
    str, PartiallyUndefinablePayloadValueTypes
]


def is_str_list(any_list: list[typing.Any]) -> typing.TypeGuard[list[str]]:
    return all(isinstance(item, str) for item in any_list)


def is_not_undefined(undefinable: UndefinedOr[_T_co]) -> typing.TypeGuard[_T_co]:
    return undefinable is not UNDEFINED


def is_payload_list(
    any_list: list[typing.Any],
) -> typing.TypeGuard[list[PayloadType]]:
    return all(isinstance(item, dict) for item in any_list)


def is_payload_list_nullable(
    any_list_nullable: list[typing.Any] | None,
) -> typing.TypeGuard[list[PayloadType] | None]:
    return (
        True
        if any_list_nullable is None
        else all(isinstance(item, dict) for item in any_list_nullable)
    )
