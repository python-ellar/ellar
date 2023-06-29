from ellar.common import GuardCanActivate, IExecutionContext
from ellar.di import injectable


@injectable
class HomeGuard(GuardCanActivate):
    async def can_activate(self, context: IExecutionContext) -> bool:
        return True
