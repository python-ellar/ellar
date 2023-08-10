from ellar.common import Serializer


class UserSchema(Serializer):
    id: str
    username: str
    password: str
