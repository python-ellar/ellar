import typing as t
from abc import ABC, abstractmethod

from ellar.common import Identity, IExecutionContext
from ellar.common.exceptions import APIException
from ellar.common.interfaces import IHostContext
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
    HTTPBasicCredentials,
)
from starlette.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.connection import HTTPConnection
    from ellar.core.routing import RouteOperation


class BaseAuth(ABC):
    exception_class: t.Union[t.Type[HTTPException], t.Type[APIException]] = APIException
    detail: str = "Forbidden"
    status_code = HTTP_401_UNAUTHORIZED

    openapi_scope: t.List = []
    openapi_in: t.Optional[str] = None
    openapi_description: t.Optional[str] = None
    openapi_name: t.Optional[str] = None

    @abstractmethod
    async def _authentication_check(
        self,
        *,
        connection: "HTTPConnection",
        context: t.Union[IHostContext, IExecutionContext],
    ) -> t.Optional[t.Any]:
        """Override and Provide Authentication actions"""

    @classmethod
    @abstractmethod
    def openapi_security_scheme(
        cls, route: t.Optional["RouteOperation"] = None
    ) -> t.Dict:
        """Override and provide OPENAPI Security Scheme"""

    async def run_authentication_check(self, context: IHostContext) -> t.Any:
        connection = context.switch_to_http_connection().get_client()
        result = await self._authentication_check(
            connection=connection, context=context
        )
        return self.handle_authentication_result(connection, result)

    def handle_invalid_request(self) -> t.Any:
        raise self.exception_class(status_code=self.status_code, detail=self.detail)

    def handle_authentication_result(
        self, connection: "HTTPConnection", result: t.Optional[t.Any]
    ) -> t.Any:
        if result:
            # auth parameter on request
            if isinstance(result, dict):
                connection.scope["user"] = Identity(**result)
            else:
                if isinstance(result, bool):
                    return result
                connection.scope["user"] = result
            return True
        return False


class BaseAPIKey(BaseAuth, ABC):
    exception_class = APIException
    parameter_name: str = "key"

    def __init__(self) -> None:
        self.name = self.parameter_name
        super().__init__()

    async def _authentication_check(
        self,
        connection: "HTTPConnection",
        context: t.Union[IHostContext, IExecutionContext],
    ) -> t.Optional[t.Any]:
        key = self._get_key(connection)
        if not key:
            return self.handle_invalid_request()
        return await self.authentication_handler(context, key)

    @abstractmethod
    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        pass  # pragma: no cover

    @abstractmethod
    async def authentication_handler(
        self,
        context: t.Union[IHostContext, IExecutionContext],
        key: t.Optional[t.Any],
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover

    @classmethod
    def openapi_security_scheme(
        cls, route: t.Optional["RouteOperation"] = None
    ) -> t.Dict:
        assert cls.openapi_in, "openapi_in is required"
        return {
            cls.openapi_name or cls.__name__: {
                "type": "apiKey",
                "description": cls.openapi_description,
                "in": cls.openapi_in,
                "name": cls.parameter_name,
            }
        }


class BaseHttpAuth(BaseAuth, ABC):
    scheme: t.Optional[str] = None
    realm: t.Optional[str] = None

    @classmethod
    def _authorization_partitioning(
        cls, authorization: t.Optional[str]
    ) -> t.Tuple[t.Optional[str], t.Optional[str], t.Optional[str]]:
        if authorization:
            return authorization.partition(" ")
        return None, None, None

    @abstractmethod
    async def authentication_handler(
        self,
        context: t.Union[IHostContext, IExecutionContext],
        credentials: t.Any,
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover

    async def _authentication_check(
        self,
        connection: "HTTPConnection",
        context: t.Union[IHostContext, IExecutionContext],
    ) -> t.Optional[t.Any]:
        credentials = self._get_credentials(connection)
        return await self.authentication_handler(context, credentials)

    @abstractmethod
    def _get_credentials(
        self, connection: "HTTPConnection"
    ) -> t.Union[HTTPBasicCredentials, HTTPAuthorizationCredentials]:
        pass  # pragma: no cover

    @classmethod
    def openapi_security_scheme(
        cls, route: t.Optional["RouteOperation"] = None
    ) -> t.Dict:
        assert cls.scheme, "openapi_scheme is required"
        return {
            cls.openapi_name or cls.__name__: {
                "type": "http",
                "description": cls.openapi_description,
                "scheme": cls.scheme,
                "name": cls.openapi_name or cls.__name__,
            }
        }
