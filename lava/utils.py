import urllib.parse as parse


def remove_null_values(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}
