import typing as t

from ellar.constants import EXTRA_ROUTE_ARGS_KEY
from ellar.core.params import ExtraEndpointArg

from .base import set_metadata as set_meta


def extra_args(*args: ExtraEndpointArg) -> t.Callable:
    """
    =========FUNCTION DECORATOR ==============

    Programmatically adds extra route function parameter.
    see https://github.com/eadwinCode/ellar/blob/main/tests/test_routing/test_extra_args.py for usages
    :param args: Collection ExtraEndpointArg
    :return:
    """
    return set_meta(EXTRA_ROUTE_ARGS_KEY, list(args))
