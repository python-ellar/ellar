import typing as t

from ellar.auth import Policy, PolicyWithRequirement
from ellar.common import IExecutionContext
from ellar.di import injectable


@injectable
class AtLeast21(PolicyWithRequirement):
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        for _k, v in requirement.items():
            assert v in context.user.requirements
        return int(context.user.get("age")) >= 21


@injectable
class AdultOnly(Policy):
    async def handle(self, context: IExecutionContext) -> bool:
        return int(context.user.get("age")) >= 18
