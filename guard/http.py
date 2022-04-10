import binascii
import typing as t
from abc import ABC, abstractmethod, ABCMeta
from base64 import b64decode

from pydantic import BaseModel
from starletteapi.requests import HTTPConnection
from starletteapi.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

from .base import BaseAuthGuard
from ..exceptions import APIException, AuthenticationFailed

__all__ = ['BaseHttpAuth', 'HttpBearerAuth', 'HttpBasicAuth', 'HttpDigestAuth']


class HTTPBasicCredentials(BaseModel):
    username: str
    password: str


class HTTPAuthorizationCredentials(BaseModel):
    scheme: str
    credentials: str


class BaseHttpAuth(BaseAuthGuard, ABC, metaclass=ABCMeta):
    openapi_description: t.Optional[str] = None
    openapi_scheme: str = None
    realm: t.Optional[str] = None

    @classmethod
    def authorization_partitioning(cls, authorization) -> t.Tuple[t.Optional[str], t.Optional[str], t.Optional[str]]:
        if authorization:
            return authorization.partition(" ")
        return None, None, None

    @abstractmethod
    async def authenticate(
            self, connection: HTTPConnection,
            credentials: t.Union[HTTPBasicCredentials, HTTPAuthorizationCredentials]
    ) -> t.Optional[t.Any]:
        pass  # pragma: no cover

    async def handle_request(self, connection: HTTPConnection) -> t.Optional[t.Any]:
        credentials = self._get_credentials(connection)
        return await self.authenticate(connection, credentials)

    @abstractmethod
    def _get_credentials(self, connection: HTTPConnection) -> t.Union[
        HTTPBasicCredentials, HTTPAuthorizationCredentials
    ]:
        pass  # pragma: no cover

    @classmethod
    def get_guard_scheme(cls) -> t.Dict:
        assert cls.openapi_scheme, 'openapi_scheme is required'
        return {
            'type': 'http',
            'description': cls.openapi_description,
            'scheme': cls.openapi_scheme,
            'name': cls.__name__
        }


class HttpBearerAuth(BaseHttpAuth, ABC):
    openapi_scheme: str = "bearer"
    openapi_bearer_format: t.Optional[str] = None
    header: str = "Authorization"

    @classmethod
    def get_guard_scheme(cls) -> t.Dict:
        scheme = super().get_guard_scheme()
        scheme.update(bearerFormat=cls.openapi_bearer_format)
        return scheme

    def _get_credentials(self, connection: HTTPConnection) -> HTTPAuthorizationCredentials:
        authorization: str = connection.headers.get(self.header)
        scheme, _, credentials = self.authorization_partitioning(authorization)
        if not (authorization and scheme and credentials):
            raise APIException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        if scheme.lower() != self.openapi_scheme:
            raise APIException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials",
            )
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


class HttpBasicAuth(BaseHttpAuth, ABC):
    openapi_scheme: str = "basic"
    realm: t.Optional[str] = None
    header = "Authorization"

    def _not_unauthorized_exception(self, message: str) -> None:
        if self.realm:
            unauthorized_headers = {"WWW-Authenticate": f'Basic realm="{self.realm}"'}
        else:
            unauthorized_headers = {"WWW-Authenticate": "Basic"}
        raise AuthenticationFailed(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=message,
            headers=unauthorized_headers,
        )

    def _get_credentials(self, connection: HTTPConnection) -> HTTPBasicCredentials:
        authorization: str = connection.headers.get(self.header)
        scheme, _, credentials = self.authorization_partitioning(authorization)

        if not authorization or scheme.lower() != self.openapi_scheme:
            raise APIException(
                status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
            )
        try:
            data = b64decode(credentials).decode("ascii")
            username, separator, password = data.partition(":")
            if not separator:
                self._not_unauthorized_exception("Invalid authentication credentials")
            return HTTPBasicCredentials(username=username, password=password)
        except (ValueError, UnicodeDecodeError, binascii.Error):
            self._not_unauthorized_exception("Invalid authentication credentials")


class HttpDigestAuth(HttpBearerAuth, ABC):
    openapi_scheme = "digest"
    header = "Authorization"
