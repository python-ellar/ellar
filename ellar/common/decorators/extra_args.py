import typing as t

from ellar.common.constants import EXTRA_ROUTE_ARGS_KEY

from .base import set_metadata as set_meta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.params import ExtraEndpointArg


def extra_args(*args: "ExtraEndpointArg") -> t.Callable:
    """
    =========FUNCTION DECORATOR ==============

    **Programmatically** adds extra route function parameter.

    :param args: Collection ExtraEndpointArg

    ### Example

    ```python
    from ellar.common import extra_args, Query
    from ellar.common.params import ExtraEndpointArg

    @get("/")
    @extra_args(ExtraEndpointArg(name="query1", annotation=str, default_value=Query()))
    def index(q: str):
        return {"q": q}
    ```
    """
    return set_meta(EXTRA_ROUTE_ARGS_KEY, list(args))
