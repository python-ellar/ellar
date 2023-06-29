from ellar.auth import IAuthorizationRequirement
from ellar.common import IExecutionContext
from ellar.di import injectable


@injectable
class AtLeast21(IAuthorizationRequirement):
    async def handle(self, context: IExecutionContext) -> bool:
        return int(context.user.get("age")) >= 21
