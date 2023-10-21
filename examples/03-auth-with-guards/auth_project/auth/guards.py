import typing as t

from ellar.auth import UserIdentity
from ellar.common import GuardCanActivate, IExecutionContext
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
    HTTPBasicCredentials,
)
from ellar.core.guards import GuardHttpBearerAuth
from ellar.di import injectable
from ellar_jwt import JWTService

if t.TYPE_CHECKING:
    from ellar.core import HTTPConnection


@injectable
class AuthGuard(GuardHttpBearerAuth):
    def __init__(self, jwt_service: JWTService) -> None:
        self.jwt_service = jwt_service

    async def authentication_handler(
        self,
        connection: "HTTPConnection",
        credentials: t.Union[HTTPBasicCredentials, HTTPAuthorizationCredentials],
    ) -> t.Optional[t.Any]:
        try:
            data = await self.jwt_service.decode_async(credentials.credentials)
            return UserIdentity(auth_type="bearer", **dict(data))
        except Exception:
            self.raise_exception()


@injectable
class AllowAnyGuard(GuardCanActivate):
    async def can_activate(self, context: IExecutionContext) -> bool:
        return True
