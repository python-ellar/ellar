import typing as t
from functools import partial

from ellar.common import APIException, EllarInterceptor, IExecutionContext
from ellar.di import injectable
from starlette import status

from .constants import POLICY_KEYS
from .policy import BasePolicyHandler, PolicyType


@injectable
class AuthorizationInterceptor(EllarInterceptor):
    status_code = status.HTTP_403_FORBIDDEN
    exception_class = APIException

    __slots__ = ()

    @t.no_type_check
    def get_route_handler_policy(
        self, context: IExecutionContext
    ) -> t.Optional[t.List[t.Union[PolicyType, str]]]:
        return context.get_app().reflector.get_all_and_override(
            POLICY_KEYS, context.get_handler(), context.get_class()
        )

    def _get_policy_instance(
        self, context: IExecutionContext, policy: t.Union[t.Type, t.Any, str]
    ) -> t.Union[BasePolicyHandler, t.Any]:
        if isinstance(policy, type):
            return context.get_service_provider().get(policy)
        return policy

    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        if not context.user.is_authenticated:
            raise self.exception_class(status_code=401)

        policies = self.get_route_handler_policy(context)

        if not policies:
            return await next_interceptor()

        partial_get_policy_instance = partial(self._get_policy_instance, context)

        for policy in map(partial_get_policy_instance, policies):
            result = await policy.handle(context)

            if not result:
                self.raise_exception()

        return await next_interceptor()

    def raise_exception(self) -> None:
        raise self.exception_class(status_code=self.status_code)
