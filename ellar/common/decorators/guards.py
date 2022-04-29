import typing as t

from ellar.constants import GUARDS_KEY

from .base import set_meta

if t.TYPE_CHECKING:
    from ellar.core.guard import GuardCanActivate


def guards(
    *_guards: t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]
) -> t.Callable:
    return set_meta(GUARDS_KEY, _guards)
