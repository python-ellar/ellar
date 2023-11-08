import typing as t

from ellar.common import GuardCanActivate, IExecutionContext


class GuardAuthMixin(GuardCanActivate):
    run_authentication_check: t.Callable[..., t.Coroutine]
    status_code = 401

    @t.no_type_check
    async def can_activate(self, context: IExecutionContext) -> bool:
        return await self.run_authentication_check(context)
