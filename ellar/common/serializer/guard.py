from .base import Serializer


class HTTPBasicCredentials(Serializer):
    username: str
    password: str


class HTTPAuthorizationCredentials(Serializer):
    scheme: str
    credentials: str
