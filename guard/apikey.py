from abc import ABC, abstractmethod
from typing import Optional, Any
from starletteapi.requests import HTTPConnection

from .base import AuthGuard


class APIKeyBase(AuthGuard, ABC):
    openapi_type: str = "apiKey"
    param_name: str = "key"

    def __init__(self) -> None:
        self.openapi_name = self.param_name
        super().__init__()

    async def handle_request(self,  connection: HTTPConnection) -> Optional[Any]:
        key = self._get_key(connection)
        return self.authenticate(connection, key)

    @abstractmethod
    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        pass  # pragma: no cover

    @abstractmethod
    def authenticate(self, connection: HTTPConnection, key: Optional[str]) -> Optional[Any]:
        pass  # pragma: no cover


class APIKeyQuery(APIKeyBase, ABC):
    openapi_in: str = "query"

    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        return connection.query_params.get(self.param_name)


class APIKeyCookie(APIKeyBase, ABC):
    openapi_in: str = "cookie"

    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        return connection.cookies.get(self.param_name)


class APIKeyHeader(APIKeyBase, ABC):
    openapi_in: str = "header"

    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        api_key: str = connection.headers.get(self.param_name)
        return api_key

