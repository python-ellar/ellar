import typing as t

from .base import set_meta

if t.TYPE_CHECKING:
    from architek.core.guard import GuardCanActivate


def guards(
    *_guards: t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
) -> t.Callable:
    return set_meta("route_guards", _guards)
