import typing as t

import starlette.status
from ellar.common import GuardCanActivate, IExecutionContext, constants
from ellar.core.services import reflector

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.routing import RouteOperation


class AuthenticatedRequiredGuard(GuardCanActivate):
    status_code = starlette.status.HTTP_401_UNAUTHORIZED

    def __init__(
        self, authentication_scheme: t.Optional[str], openapi_scope: t.List
    ) -> None:
        self.authentication_scheme = authentication_scheme
        self.openapi_scope = openapi_scope or []

    def openapi_security_scheme(
        self, route: t.Optional["RouteOperation"] = None
    ) -> t.Dict:
        # this will only add security scope to the applied controller or route function
        skip_auth: t.Any = False
        if route:
            skip_auth = reflector.get_all_and_override(
                constants.SKIP_AUTH, route.endpoint, route.get_controller_type()
            )
        if not skip_auth and self.authentication_scheme:
            return {self.authentication_scheme: {}}

        return {}

    async def can_activate(self, context: IExecutionContext) -> bool:
        skip_auth = reflector.get_all_and_override(
            constants.SKIP_AUTH, context.get_handler(), context.get_class()
        )

        if skip_auth:
            return True
        return context.user.is_authenticated
