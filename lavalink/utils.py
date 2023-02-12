import typing

import lavalink.types as types


_T1 = typing.TypeVar("_T1", bound=typing.Any)
_T2 = typing.TypeVar("_T2", bound=typing.Any)


def remove_undefined_values(
    kwargs: types.PartiallyUndefinablePayloadType,
) -> types.PayloadType:
    return {k: v for k, v in kwargs.items() if types.is_not_undefined(v)}


def and_then(value: types.UndefinedOr[_T1], func: typing.Callable[[_T1], _T2]) -> types.UndefinedOr[_T2]:
    if not types.is_not_undefined(value):
        return value
    
    return func(value)