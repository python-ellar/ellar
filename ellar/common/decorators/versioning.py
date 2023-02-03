import typing as t

from ellar.constants import VERSIONING_KEY

from .base import set_metadata as set_meta


def version(*_version: str) -> t.Callable:
    """
     ========= ROUTE FUNCTION DECORATOR ==============

     Defines route function version
    :param _version: allowed versions
    :return:
    """
    return set_meta(VERSIONING_KEY, set([str(i) for i in _version]))
