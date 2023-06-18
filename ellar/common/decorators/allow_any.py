import typing as t

from ellar.common.constants import GUARDS_KEY
from ellar.di import injectable

from ..models import GuardCanActivate
from .base import set_metadata as set_meta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import IExecutionContext


@injectable
class AllowAnyGuard(GuardCanActivate):
    async def can_activate(self, context: "IExecutionContext") -> bool:
        return True


def allow_any_guard(func_or_class: t.Any) -> t.Callable:
    target_decorator = set_meta(GUARDS_KEY, [AllowAnyGuard])
    return target_decorator(func_or_class)  # type: ignore[no-any-return]
