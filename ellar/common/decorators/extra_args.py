import typing as t

from ellar.common.constants import EXTRA_ROUTE_ARGS_KEY

from .base import set_metadata as set_meta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.params import ExtraEndpointArg


def extra_args(*args: "ExtraEndpointArg") -> t.Callable:
    """
    =========FUNCTION DECORATOR ==============

    Programmatically adds extra route function parameter.
    see https://github.com/eadwinCode/ellar/blob/main/tests/test_routing/test_extra_args.py for usages
    :param args: Collection ExtraEndpointArg
    :return:
    """
    return set_meta(EXTRA_ROUTE_ARGS_KEY, list(args))
