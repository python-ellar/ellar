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

from ellar.di import injectable
from ellar_jwt import JWTService
from starlette import status
from starlette.exceptions import HTTPException

from ..users.services import UserService
from .schemas import UserCredentials


@injectable
class AuthService:
    def __init__(self, user_service: UserService, jwt_service: JWTService):
        self.user_service = user_service
        self.jwt_service = jwt_service

    async def sign_in(self, credentials: UserCredentials) -> t.Dict:
        user = await self.user_service.find_one(credentials.username)
        if user.password != credentials.password:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        return {"access_token": await self.jwt_service.sign_async(user.dict())}
