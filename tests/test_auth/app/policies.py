import typing as t

from ellar.auth import BasePolicyHandler, BasePolicyHandlerWithRequirement
from ellar.common import IExecutionContext
from ellar.di import injectable


@injectable
class AtLeast21(BasePolicyHandlerWithRequirement):
    async def handle(self, context: IExecutionContext, requirement: t.Any) -> bool:
        return int(context.user.get("age")) >= 21


@injectable
class AdultOnly(BasePolicyHandler):
    async def handle(self, context: IExecutionContext) -> bool:
        return int(context.user.get("age")) >= 18
