import typing as t

from ellar.auth.policy.base import BasePolicyHandlerWithRequirement
from ellar.common import IExecutionContext
from ellar.di import injectable


@injectable
class AtLeast21(BasePolicyHandlerWithRequirement):
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        return int(context.user.get("age")) >= 21
