import typing as t
from abc import ABC, ABCMeta, abstractmethod

from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from ellar.core.connection import HTTPConnection
from ellar.core.context import IExecutionContext
from ellar.core.exceptions import APIException


class GuardCanActivate(ABC, metaclass=ABCMeta):
    exception_class: t.Union[
        t.Type[HTTPException], t.Type[APIException]
    ] = HTTPException
    status_code: int = HTTP_403_FORBIDDEN
    detail: str = "Not authenticated"

    @abstractmethod
    async def can_activate(self, context: IExecutionContext) -> bool:
        pass

    def raise_exception(self) -> None:
        raise self.exception_class(status_code=self.status_code, detail=self.detail)


class BaseAuthGuard(GuardCanActivate, ABC, metaclass=ABCMeta):
    status_code = HTTP_401_UNAUTHORIZED
    openapi_scope: t.List = []
    openapi_in: t.Optional[str] = None
    openapi_description: t.Optional[str] = None
    openapi_name: t.Optional[str] = None

    @abstractmethod
    async def handle_request(self, *, connection: HTTPConnection) -> t.Optional[t.Any]:
        pass

    @classmethod
    @abstractmethod
    def get_guard_scheme(cls) -> t.Dict:
        pass

    async def can_activate(self, context: IExecutionContext) -> bool:
        connection = context.switch_to_http_connection().get_client()
        result = await self.handle_request(connection=connection)
        if result:
            # auth parameter on request
            connection.scope["user"] = result
            return True
        return False


class HTTPBasicCredentials(BaseModel):
    username: str
    password: str


class HTTPAuthorizationCredentials(BaseModel):
    scheme: str
    credentials: str


class BaseAPIKey(BaseAuthGuard, ABC, metaclass=ABCMeta):
    exception_class = APIException
    parameter_name: str = "key"

    def __init__(self) -> None:
        self.name = self.parameter_name
        super().__init__()

    async def handle_request(self, connection: HTTPConnection) -> t.Optional[t.Any]:
        key = self._get_key(connection)
        if not key:
            self.raise_exception()
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
            "name": cls.openapi_name or cls.__name__,
        }


class BaseHttpAuth(BaseAuthGuard, ABC, metaclass=ABCMeta):
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
            "name": cls.openapi_name or cls.__name__,
        }
