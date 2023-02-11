import lavalink.types as types


def remove_null_values(
    kwargs: types.NullablePayloadType,
) -> types.PartiallyNullablePayloadType:
    return {k: v for k, v in kwargs.items() if v is not None}
