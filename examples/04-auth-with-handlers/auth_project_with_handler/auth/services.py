"""
Create a provider and declare its scope

@injectable
class AProvider
    pass

@injectable(scope=transient_scope)
class BProvider
    pass
"""
import typing as t
from datetime import timedelta

from ellar.common import exceptions
from ellar.core.security.hashers import check_password
from ellar.di import injectable
from ellar_jwt import JWTService

from ..users.services import UsersService


@injectable()
class AuthService:
    def __init__(self, users_service: UsersService, jwt_service: JWTService) -> None:
        self.users_service = users_service
        self.jwt_service = jwt_service

    async def sign_in(self, username: str, password: str) -> t.Any:
        user_model = await self.users_service.get_user_by_username(username)
        if user_model is None:
            raise exceptions.AuthenticationFailed()

        if not check_password(password, user_model.password):
            raise exceptions.AuthenticationFailed()

        result = {
            "access_token": await self.jwt_service.sign_async(
                payload=dict(user_model.serialize(), sub=user_model.user_id)
            ),
            "refresh_token": await self.jwt_service.sign_async(
                payload={"sub": user_model.username}, lifetime=timedelta(days=30)
            ),
        }
        return result

    async def refresh_token(self, refresh_token: str) -> t.Dict:
        try:
            payload = await self.jwt_service.decode_async(refresh_token)
        except Exception as ex:
            raise exceptions.AuthenticationFailed() from ex

        user_model = await self.users_service.get_user_by_username(payload["sub"])
        if user_model is None:
            raise exceptions.AuthenticationFailed()

        return {
            "access_token": await self.jwt_service.sign_async(
                payload=dict(user_model.serialize(), sub=user_model.user_id)
            ),
        }
