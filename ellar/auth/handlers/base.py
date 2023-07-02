import typing as t
from abc import abstractmethod

from ellar.common import Identity, IHostContext
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
    HTTPBasicCredentials,
)

from ..auth_handler import BaseAuthenticationHandler

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import HTTPConnection


class BaseAPIKeyAuthenticationHandler(BaseAuthenticationHandler):
    scheme: str = "apiKey"
    openapi_name: t.Optional[str] = None
    openapi_description: t.Optional[str] = None
    openapi_in: t.Optional[str] = None
    parameter_name: str = "key"

    @classmethod
    def openapi_security_scheme(cls) -> t.Dict:
        assert cls.openapi_in, "openapi_in is required"
        return {
            cls.openapi_name
            or cls.__name__: {
                "type": "apiKey",
                "description": cls.openapi_description,
                "in": cls.openapi_in,
                "name": cls.parameter_name,
            }
        }

    @abstractmethod
    def _get_key(self, connection: "HTTPConnection") -> t.Optional[t.Any]:
        pass  # pragma: no cover

    async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
        key = self._get_key(context.switch_to_http_connection().get_client())
        if not key:
            return None
        return await self.handle_authentication(context, key)

    @abstractmethod
    async def handle_authentication(
        self, context: IHostContext, key: str
    ) -> t.Optional[Identity]:
        pass  # pragma: no cover


class BaseHttpAuthenticationHandler(BaseAuthenticationHandler):
    scheme: str = "http"
    openapi_scheme: t.Optional[str] = None
    openapi_name: t.Optional[str] = None
    openapi_description: t.Optional[str] = None

    @classmethod
    def openapi_security_scheme(cls) -> t.Dict:
        return {
            cls.openapi_name
            or cls.__name__: {
                "type": "http",
                "description": cls.openapi_description,
                "scheme": cls.openapi_scheme or cls.scheme,
                "name": cls.openapi_name or cls.__name__,
            }
        }

    @classmethod
    def authorization_partitioning(
        cls, authorization: t.Optional[str]
    ) -> t.Tuple[t.Optional[str], t.Optional[str], t.Optional[str]]:
        if authorization:
            return authorization.partition(" ")
        return None, None, None

    @abstractmethod
    async def handle_authentication(
        self,
        context: IHostContext,
        credentials: t.Optional[
            t.Union[HTTPBasicCredentials, HTTPAuthorizationCredentials]
        ],
    ) -> t.Optional[Identity]:
        pass  # pragma: no cover

    @abstractmethod
    def _get_credentials(
        self, connection: "HTTPConnection"
    ) -> t.Optional[t.Union[HTTPBasicCredentials, HTTPAuthorizationCredentials]]:
        pass  # pragma: no cover

    async def authenticate(self, context: IHostContext) -> t.Optional[Identity]:
        credentials = self._get_credentials(
            context.switch_to_http_connection().get_client()
        )
        if not credentials:
            return None
        return await self.handle_authentication(context, credentials)
