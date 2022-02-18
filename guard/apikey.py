from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from starlette.status import HTTP_403_FORBIDDEN
from starletteapi.requests import HTTPConnection

from .base import BaseAuthGuard

__all__ = ['BaseAPIKey', 'APIKeyQuery', 'APIKeyCookie', 'APIKeyHeader']

from ..exceptions import APIException


class BaseAPIKey(BaseAuthGuard, ABC):
    openapi_in: str = None
    parameter_name: str = "key"
    openapi_description: Optional[str] = None

    def __init__(self) -> None:
        self.name = self.parameter_name
        super().__init__()

    async def handle_request(self, connection: HTTPConnection) -> Optional[Any]:
        key = self._get_key(connection)
        if not key:
            raise APIException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        return await self.authenticate(connection, key)

    @abstractmethod
    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        pass  # pragma: no cover

    @abstractmethod
    async def authenticate(self, connection: HTTPConnection, key: Optional[str]) -> Optional[Any]:
        pass  # pragma: no cover

    @classmethod
    def get_guard_scheme(cls) -> Dict:
        assert cls.openapi_in, 'openapi_in is required'
        return {
            'type': 'apiKey',
            'description': cls.openapi_description,
            'in': cls.openapi_in,
            'name': cls.__name__
        }


class APIKeyQuery(BaseAPIKey, ABC):
    openapi_in: str = "query"

    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        return connection.query_params.get(self.parameter_name)


class APIKeyCookie(BaseAPIKey, ABC):
    openapi_in: str = "cookie"

    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        return connection.cookies.get(self.parameter_name)


class APIKeyHeader(BaseAPIKey, ABC):
    openapi_in: str = "header"

    def _get_key(self, connection: HTTPConnection) -> Optional[str]:
        return connection.headers.get(self.parameter_name)
