import typing as t

from architek.constants import GUARDS_KEY

from .base import set_meta

if t.TYPE_CHECKING:
    from architek.core.guard import GuardCanActivate


def guards(
    *_guards: t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
) -> t.Callable:
    return set_meta(GUARDS_KEY, _guards)
