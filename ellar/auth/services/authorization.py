import asyncio
import typing as t
from functools import partial

from ellar.common import IExecutionContext
from ellar.di import injectable

from ..interfaces import IAuthorizationConfig, IAuthorizationRequirement
from ..requirements import AuthorizationRequirementType


@injectable
class AuthorizationService:
    __slots__ = ("authorization_config",)

    def __init__(self, authorization_config: IAuthorizationConfig) -> None:
        self.authorization_config = authorization_config

    def get_requirement_object(
        self, context: IExecutionContext, requirement: AuthorizationRequirementType
    ) -> IAuthorizationRequirement:
        if isinstance(requirement, type):
            return t.cast(
                IAuthorizationRequirement,
                context.get_service_provider().get(requirement),
            )
        return requirement

    async def authorize_with_policy(
        self, context: IExecutionContext, policy_name: str
    ) -> bool:
        policy = self.authorization_config.find_policy(policy_name)
        return await self.authorize_with_requirements(context, policy.requirements)

    async def authorize_with_requirements(
        self,
        context: IExecutionContext,
        requirements: t.Sequence[AuthorizationRequirementType],
    ) -> bool:
        get_requirement_object_partial = partial(self.get_requirement_object, context)

        requirement_objects = map(get_requirement_object_partial, requirements)

        for item in requirement_objects:
            if asyncio.iscoroutinefunction(item.handle):
                result = await item.handle(context)
            else:
                result = item.handle(context)  # type: ignore[misc, assignment]

            if not result:
                return False

        return True
