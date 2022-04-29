import typing as t

from architek.constants import VERSIONING_KEY

from .base import set_meta


def version(*_version: str) -> t.Callable:
    return set_meta(VERSIONING_KEY, set(_version))
