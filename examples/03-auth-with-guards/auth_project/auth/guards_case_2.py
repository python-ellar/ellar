import typing as t

from ellar.auth import UserIdentity
from ellar.auth.guards import GuardHttpBearerAuth
from ellar.common import IExecutionContext, logger, set_metadata
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
)
from ellar.core import Reflector
from ellar.di import injectable
from ellar_jwt import JWTService

IS_ANONYMOUS = "is_anonymous"


def allow_any() -> t.Callable:
    return set_metadata(IS_ANONYMOUS, True)


@injectable
class AuthGuard(GuardHttpBearerAuth):
    def __init__(self, jwt_service: JWTService, reflector: Reflector) -> None:
        self.jwt_service = jwt_service
        self.reflector = reflector

    async def authentication_handler(
        self,
        context: IExecutionContext,
        credentials: HTTPAuthorizationCredentials,
    ) -> t.Optional[t.Any]:
        is_anonymous = self.reflector.get_all_and_override(
            IS_ANONYMOUS, context.get_handler(), context.get_class()
        )

        if is_anonymous:
            return True

        try:
            data = await self.jwt_service.decode_async(credentials.credentials)
            return UserIdentity(auth_type=self.scheme, **data)
        except Exception as ex:
            logger.logger.error(f"[AuthGuard] Exception: {ex}")
            self.raise_exception()
