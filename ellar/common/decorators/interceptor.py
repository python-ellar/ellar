import typing as t

from ellar.common.constants import ROUTE_INTERCEPTORS

from .base import set_metadata as set_meta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import EllarInterceptor


def UseInterceptors(
    *args: t.Union[t.Type["EllarInterceptor"], "EllarInterceptor"]
) -> t.Callable:
    """
    =========CONTROLLER AND FUNCTION DECORATOR ==============

    Decorator that binds interceptors to the scope of the controller or method,
    depending on its context.

    When `@UseInterceptors` is used at the controller level, the interceptor will
    be applied to every handler (method) in the controller.

    When `@UseInterceptors` is used at the individual handler level, the interceptor
    will apply only to that specific method.

    Note
    Interceptors can also be set up globally for all controllers and routes
    using `app.use_global_interceptors()`.

    :param args: A single EllarInterceptor instance or class, or a list of EllarInterceptor instances or classes.
    :return:
    """
    return set_meta(ROUTE_INTERCEPTORS, list(args))
