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

from .schemas import UserSchema


@injectable
class UserService:
    users = [
        {
            "id": 1,
            "username": "chigozie",
            "password": "changeme",
        },
        {
            "id": 2,
            "username": "chinelo",
            "password": "guess",
        },
    ]

    async def find_one(self, username: str) -> t.Optional[UserSchema]:
        users_filter = [user for user in self.users if user["username"] == username]
        if users_filter:
            return UserSchema(**users_filter[0])
        return None
