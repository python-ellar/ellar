import typing as t

from ellar.common.constants import GUARDS_KEY

from .base import set_metadata as set_meta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.models import GuardCanActivate


def UseGuards(
    *_guards: t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
) -> t.Callable:
    """
    =========CONTROLLER AND ROUTE FUNCTION DECORATOR ==============

    Decorator that binds guards to the scope of the controller or method,
    depending on its context.

    When `@UseGuards` is used at the controller level, the guard will be
    applied to every handler (method) in the controller.

    When `@UseGuards` is used at the individual handler level, the guard
    will apply only to that specific method.


    Note:
    Guards can also be set up globally for all controllers and routes
    using `app.use_global_guards()`

    :param _guards: A single guard instance or class, or a list of guard instances
    or classes.
    :return:
    """
    return set_meta(GUARDS_KEY, list(_guards))
