import typing as t

import starlette.status
from ellar.common import GuardCanActivate, IExecutionContext


class AuthenticatedRequiredGuard(GuardCanActivate):
    status_code = starlette.status.HTTP_401_UNAUTHORIZED

    def __init__(
        self, authentication_scheme: t.Optional[str], openapi_scope: t.List
    ) -> None:
        self.authentication_scheme = authentication_scheme
        self.openapi_scope = openapi_scope or []

    def openapi_security_scheme(self) -> t.Dict:
        # this will only add security scope to the applied controller or route function
        if self.authentication_scheme:
            return {self.authentication_scheme: {}}

        return {}

    async def can_activate(self, context: IExecutionContext) -> bool:
        return (  # type:ignore[no-any-return]
            context.switch_to_http_connection().get_request().user.is_authenticated
        )
