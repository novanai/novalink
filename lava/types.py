import typing


AtomicTypes = None | str | int | float | bool

PayloadType = dict[
    str, AtomicTypes | list[AtomicTypes] | "PayloadType" | list["PayloadType"]
]


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
