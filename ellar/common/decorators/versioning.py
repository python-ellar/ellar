import typing as t

from ellar.common.constants import VERSIONING_KEY

from .base import set_metadata as set_meta


def Version(*_version: str) -> t.Callable:
    """
     ========= CONTROLLER AND ROUTE FUNCTION DECORATOR ==============

     Defines route function version
    :param _version: allowed versions
    :return:
    """
    return set_meta(VERSIONING_KEY, {str(i) for i in _version})
