import typing as t

import starlette.status
from ellar.common import GuardCanActivate, IExecutionContext, constants
from ellar.core import Reflector


class AuthenticatedRequiredGuard(GuardCanActivate):
    status_code = starlette.status.HTTP_401_UNAUTHORIZED

    def __init__(
        self, authentication_scheme: t.Optional[str], openapi_scope: t.List
    ) -> None:
        self.authentication_scheme = authentication_scheme
        self.openapi_scope = openapi_scope or []
        self.reflector = Reflector()

    def openapi_security_scheme(self) -> t.Dict:
        # this will only add security scope to the applied controller or route function
        if self.authentication_scheme:
            return {self.authentication_scheme: {}}

        return {}

    async def can_activate(self, context: IExecutionContext) -> bool:
        skip_auth = self.reflector.get_all_and_override(
            constants.SKIP_AUTH, context.get_handler(), context.get_class()
        )

        if skip_auth:
            return True
        return context.user.is_authenticated
