import typing


_T = typing.TypeVar("_T")
MaybeSequence = _T | typing.Sequence[_T]
AwaitableNull = typing.Coroutine[typing.Any, typing.Any, None]

AtomicTypes = str | int | float | bool
NullableAtomicTypes = AtomicTypes | None

PayloadValueTypes = MaybeSequence[AtomicTypes] | MaybeSequence["PayloadType"]
NullablePayloadValueTypes = (
    MaybeSequence[NullableAtomicTypes] | MaybeSequence["NullablePayloadType"]
)
PartiallyNullablePayloadValueTypes = (
    AtomicTypes
    | typing.Sequence[NullableAtomicTypes]
    | MaybeSequence["NullablePayloadType"]
)

PayloadType = typing.Mapping[str, PayloadValueTypes]
NullablePayloadType = typing.Mapping[str, NullablePayloadValueTypes]
PartiallyNullablePayloadType = typing.Mapping[str, PartiallyNullablePayloadValueTypes]
MutablePayloadType = typing.MutableMapping[str, PayloadValueTypes]
MutableNullablePayloadType = typing.MutableMapping[str, NullablePayloadValueTypes]


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


def is_str_list(any_list: list[typing.Any]) -> typing.TypeGuard[list[str]]:
    return all(isinstance(item, str) for item in any_list)
