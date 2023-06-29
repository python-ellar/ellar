import typing as t
from functools import partial

from starlette import status

from ellar.common import APIException, GuardCanActivate, IExecutionContext
from ellar.di import injectable

from .constants import POLICY_KEYS
from .policy import Policy
from .services import AuthorizationService

_PolicyType = t.Union[Policy, t.Type[Policy]]


@injectable
class AuthorizationGuard(GuardCanActivate):
    status_code = status.HTTP_403_FORBIDDEN
    exception_class = APIException

    __slots__ = ("authorization_service",)

    def __init__(self, authorization_service: AuthorizationService) -> None:
        self.authorization_service = authorization_service

    @t.no_type_check
    def get_route_handler_policy(
        self, context: IExecutionContext
    ) -> t.Optional[t.List[t.Union[_PolicyType, str]]]:
        return context.get_app().reflector.get_all_and_override(
            POLICY_KEYS, context.get_handler(), context.get_class()
        )

    def get_policy_instance(
        self, context: IExecutionContext, policy: t.Union[t.Type, t.Any, str]
    ) -> t.Union[Policy, str, t.Any]:
        if isinstance(policy, type):
            return context.get_service_provider().get(policy)
        return policy

    async def can_activate(self, context: IExecutionContext) -> bool:
        if not context.user.is_authenticated:
            raise self.exception_class(status_code=401)

        policies = self.get_route_handler_policy(context)

        if not policies:
            return True

        partial_get_policy_instance = partial(self.get_policy_instance, context)

        for policy in map(partial_get_policy_instance, policies):
            if isinstance(policy, Policy):
                result = await self.authorization_service.authorize_with_requirements(
                    context, policy.requirements
                )
            elif isinstance(policy, str):
                result = await self.authorization_service.authorize_with_policy(
                    context, policy
                )
            else:
                raise RuntimeError(f"Unknown policy type:- {policy}")

            if not result:
                self.raise_exception()
        return True

    def raise_exception(self) -> None:
        raise self.exception_class(status_code=self.status_code)
