import typing as t

from ellar.constants import VERSIONING_KEY

from .base import set_meta


def version(*_version: str) -> t.Callable:
    return set_meta(VERSIONING_KEY, set(_version))
