import typing as t

from ellar.auth import UserIdentity
from ellar.auth.guards import GuardHttpBearerAuth
from ellar.common import (
    GuardCanActivate,
    IExecutionContext,
    constants,
    logger,
    set_metadata,
)
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
)
from ellar.di import injectable
from ellar_jwt import JWTService


def allow_any() -> t.Callable:
    return set_metadata(constants.GUARDS_KEY, [AllowAny()])


class AllowAny(GuardCanActivate):
    async def can_activate(self, context: IExecutionContext) -> bool:
        return True


@injectable
class AuthGuard(GuardHttpBearerAuth):
    def __init__(self, jwt_service: JWTService) -> None:
        self.jwt_service = jwt_service

    async def authentication_handler(
        self,
        context: IExecutionContext,
        credentials: HTTPAuthorizationCredentials,
    ) -> t.Optional[t.Any]:
        try:
            data = await self.jwt_service.decode_async(credentials.credentials)
            return UserIdentity(auth_type="bearer", **data)
        except Exception as ex:
            logger.logger.error(f"[AuthGuard] Exception: {ex}")
            self.raise_exception()
