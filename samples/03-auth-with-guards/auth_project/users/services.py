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

from ellar.core.security.hashers import make_password
from ellar.di import injectable

from .schemas import UserModel


@injectable()
class UsersService:
    users = [
        {
            "user_id": 1,
            "username": "john",
            "password": make_password("password"),
        },
        {
            "user_id": 2,
            "username": "clara",
            "password": make_password("guess"),
        },
    ]

    async def get_user_by_username(self, username: str) -> t.Optional[UserModel]:
        filtered_list = filter(lambda item: item["username"] == username, self.users)
        found_user = next(filtered_list)
        if found_user:
            return UserModel(**found_user)
