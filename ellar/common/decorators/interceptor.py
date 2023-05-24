import typing as t

from ellar.common.constants import ROUTE_INTERCEPTORS

from .base import set_metadata as set_meta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import EllarInterceptor


def interceptors(
    *args: t.Union[t.Type["EllarInterceptor"], "EllarInterceptor"]
) -> t.Callable:
    """
    =========FUNCTION DECORATOR ==============

    Programmatically adds extra route function parameter.
    see https://github.com/eadwinCode/ellar/blob/main/tests/test_routing/test_extra_args.py for usages
    :param args: Collection EllarInterceptor
    :return:
    """
    return set_meta(ROUTE_INTERCEPTORS, list(args))
