import typing as t

from .base import set_meta


def version(*_version: str) -> t.Callable:
    return set_meta("route_versioning", set(_version))
