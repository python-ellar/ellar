import typing as t

from ellar.auth import UserIdentity
from ellar.auth.handlers import HttpBearerAuthenticationHandler
from ellar.common import IHostContext
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
)
from ellar.di import injectable
from ellar_jwt import JWTService


@injectable
class JWTAuthentication(HttpBearerAuthenticationHandler):
    def __init__(self, jwt_service: JWTService) -> None:
        self.jwt_service = jwt_service

    async def authentication_handler(
        self,
        context: IHostContext,
        credentials: HTTPAuthorizationCredentials,
    ) -> t.Optional[t.Any]:
        # this function will be called by Identity Middleware but only when a `Bearer token` is found on the header request
        try:
            data = await self.jwt_service.decode_async(credentials.credentials)
            return UserIdentity(auth_type=self.scheme, **data)
        except Exception:
            return None
