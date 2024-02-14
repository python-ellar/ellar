import binascii
import typing as t
from abc import ABC
from base64 import b64decode

from ellar.common.exceptions import APIException, AuthenticationFailed
from ellar.common.serializer.guard import (
    HTTPAuthorizationCredentials,
    HTTPBasicCredentials,
)

from .base import BaseHttpAuth

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.connection import HTTPConnection
    from ellar.core.routing import RouteOperation


class HttpBearerAuth(BaseHttpAuth, ABC):
    exception_class = APIException
    scheme: str = "bearer"
    openapi_bearer_format: t.Optional[str] = None
    header: str = "Authorization"

    @classmethod
    def openapi_security_scheme(
        cls, route: t.Optional["RouteOperation"] = None
    ) -> t.Dict:
        scheme = super().openapi_security_scheme(route)
        scheme[cls.openapi_name or cls.__name__].update(
            bearerFormat=cls.openapi_bearer_format
        )
        return scheme

    def _get_credentials(
        self, connection: "HTTPConnection"
    ) -> HTTPAuthorizationCredentials:
        authorization: t.Optional[str] = connection.headers.get(self.header)
        scheme, _, credentials = self._authorization_partitioning(authorization)
        if not (authorization and scheme and credentials):
            return self.handle_invalid_request()  # type: ignore[no-any-return]
        if scheme and str(scheme).lower() != self.scheme:
            raise self.exception_class(
                status_code=self.status_code,
                detail="Invalid authentication credentials",
            )
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


class HttpBasicAuth(BaseHttpAuth, ABC):
    exception_class = APIException
    scheme: str = "basic"
    realm: t.Optional[str] = None
    header = "Authorization"

    def _not_unauthorized_exception(self, message: str) -> None:
        if self.realm:  # pragma: no cover
            unauthorized_headers = {"WWW-Authenticate": f'Basic realm="{self.realm}"'}
        else:
            unauthorized_headers = {"WWW-Authenticate": "Basic"}
        raise AuthenticationFailed(
            status_code=self.status_code,
            detail=message,
            headers=unauthorized_headers,
        )

    def _get_credentials(self, connection: "HTTPConnection") -> HTTPBasicCredentials:
        authorization: t.Optional[str] = connection.headers.get(self.header)
        parts = authorization.split(" ") if authorization else []
        scheme, credentials = str(), str()

        if len(parts) == 1:
            credentials = parts[0]
            scheme = "basic"
        elif len(parts) == 2:
            credentials = parts[1]
            scheme = parts[0].lower()

        if (
            not (authorization and scheme and credentials)
            or scheme.lower() != self.scheme
        ):
            return self.handle_invalid_request()  # type: ignore[no-any-return]

        data: t.Optional[t.Union[str, bytes]] = None
        try:
            data = b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            self._not_unauthorized_exception("Invalid authentication credentials")

        username, separator, password = (
            str(data).partition(":") if data else (None, None, None)
        )

        if not separator:
            self._not_unauthorized_exception("Invalid authentication credentials")
        return HTTPBasicCredentials(username=username, password=password)  # type: ignore[arg-type]


class HttpDigestAuth(HttpBearerAuth, ABC):
    scheme = "digest"
    header = "Authorization"
