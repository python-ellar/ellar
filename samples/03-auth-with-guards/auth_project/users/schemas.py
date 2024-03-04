from ellar.common import Serializer
from ellar.common.serializer import SerializerFilter


class UserModel(Serializer):
    _filter = SerializerFilter(exclude={"password"})

    user_id: int
    username: str
    password: str
