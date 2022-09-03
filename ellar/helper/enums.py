import typing as t
from enum import Enum


def create_enums_from_list(name: str, *keys: str) -> Enum:
    """
    Creates an Enum from list of strings
    :param name: Enum Name
    :param keys: Enum keys
    :return: `class Enum`
    """
    assert len(keys) > 0
    dict_ = {k: k for k in keys}
    enum: Enum = Enum(name, dict_)  # type: ignore
    return t.cast(Enum, enum)


def create_enums_from_dict(name: str, **kwargs: t.Any) -> Enum:
    """
    Creates an Enum from dictionary
    :param name: Enum Name
    :return: `class Enum`
    """
    assert len(kwargs) > 0
    enum: Enum = Enum(name, kwargs)  # type: ignore
    return t.cast(Enum, enum)
