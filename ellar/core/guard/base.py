import typing as t
from abc import ABC, ABCMeta, abstractmethod

from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from ellar.core.connection import HTTPConnection
from ellar.core.context import ExecutionContext
from ellar.exceptions import APIException


class GuardCanActivate(ABC, metaclass=ABCMeta):
    _exception_class: t.Type[HTTPException] = HTTPException
    _status_code: int = HTTP_403_FORBIDDEN
    _detail: str = "Not authenticated"

    @abstractmethod
    async def can_activate(self, context: ExecutionContext) -> bool:
        pass

    def raise_exception(self) -> None:
        raise self._exception_class(status_code=self._status_code, detail=self._detail)


class BaseAuthGuard(GuardCanActivate, ABC, metaclass=ABCMeta):
    openapi_scope: t.List = []

    @abstractmethod
    async def handle_request(self, *, connection: HTTPConnection) -> t.Optional[t.Any]:
        pass

    @classmethod
    @abstractmethod
    def get_guard_scheme(cls) -> t.Dict:
        pass

    async def can_activate(self, context: ExecutionContext) -> bool:
        connection = context.switch_to_http_connection()
        result = await self.handle_request(connection=connection)
        if result:
            # auth parameter on request
            return True
        return False


class HTTPBasicCredentials(BaseModel):
    username: str
    password: str


class HTTPAuthorizationCredentials(BaseModel):
    scheme: str
    credentials: str


class BaseAPIKey(BaseAuthGuard, ABC, metaclass=ABCMeta):
    openapi_in: t.Optional[str] = None
    parameter_name: str = "key"
    openapi_description: t.Optional[str] = None

    def __init__(self) -> None:
        self.name = self.parameter_name
        super().__init__()

    async def handle_request(self, connection: HTTPConnection) -> t.Optional[t.Any]:
        key = self._get_key(connection)
        if not key:
            raise APIException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        return await self.authenticate(connection, key)

    @abstractmethod
    def _get_key(self, connection: HTTPConnection) -> t.Optional[t.Any]:
        pass  # pragma: no cover

    @abstractmethod
    async def authenticate(
        self, connection: HTTPConnection, key: t.Optional[t.Any]
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover

    @classmethod
    def get_guard_scheme(cls) -> t.Dict:
        assert cls.openapi_in, "openapi_in is required"
        return {
            "type": "apiKey",
            "description": cls.openapi_description,
            "in": cls.openapi_in,
            "name": cls.__name__,
        }


class BaseHttpAuth(BaseAuthGuard, ABC, metaclass=ABCMeta):
    openapi_description: t.Optional[str] = None
    openapi_scheme: t.Optional[str] = None
    realm: t.Optional[str] = None

    @classmethod
    def authorization_partitioning(
        cls, authorization: t.Optional[str]
    ) -> t.Tuple[t.Optional[str], t.Optional[str], t.Optional[str]]:
        if authorization:
            return authorization.partition(" ")
        return None, None, None

    @abstractmethod
    async def authenticate(
        self,
        connection: HTTPConnection,
        credentials: t.Union[HTTPBasicCredentials, HTTPAuthorizationCredentials],
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover

    async def handle_request(self, connection: HTTPConnection) -> t.Optional[t.Any]:
        credentials = self._get_credentials(connection)
        return await self.authenticate(connection, credentials)

    @abstractmethod
    def _get_credentials(
        self, connection: HTTPConnection
    ) -> t.Union[HTTPBasicCredentials, HTTPAuthorizationCredentials]:
        pass  # pragma: no cover

    @classmethod
    def get_guard_scheme(cls) -> t.Dict:
        assert cls.openapi_scheme, "openapi_scheme is required"
        return {
            "type": "http",
            "description": cls.openapi_description,
            "scheme": cls.openapi_scheme,
            "name": cls.__name__,
        }
