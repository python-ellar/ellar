import typing as t

from starlette import status

from .base import APIException, ErrorDetail
from .validation import RequestValidationError, WebSocketRequestValidationError

__all__ = [
    "ImproperConfiguration",
    "APIException",
    "WebSocketRequestValidationError",
    "RequestValidationError",
    "AuthenticationFailed",
    "NotAuthenticated",
    "PermissionDenied",
    "NotFound",
    "MethodNotAllowed",
    "NotAcceptable",
    "UnsupportedMediaType",
]


class ImproperConfiguration(Exception):
    pass


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Incorrect authentication credentials."
    default_code = "authentication_failed"


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication credentials were not provided."
    default_code = "not_authenticated"


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Not found."
    default_code = "not_found"


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = 'Method "{method}" not allowed.'
    default_code = "method_not_allowed"

    def __init__(
        self,
        method: str,
        detail: t.Optional[t.Union[t.List, t.Dict, ErrorDetail, str]] = None,
        code: t.Optional[t.Union[str, int]] = None,
    ):
        if detail is None:
            detail = str(self.default_detail).format(method=method)
        super().__init__(detail, code)


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "Could not satisfy the request Accept header."
    default_code = "not_acceptable"

    def __init__(
        self,
        detail: t.Optional[t.Union[t.List, t.Dict, ErrorDetail, str]] = None,
        code: t.Optional[t.Union[str, int]] = None,
        available_renderers: t.Optional[str] = None,
    ):
        self.available_renderers = available_renderers
        super().__init__(detail, code)


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = 'Unsupported media type "{media_type}" in request.'
    default_code = "unsupported_media_type"

    def __init__(
        self,
        media_type: str,
        detail: t.Optional[t.Union[t.List, t.Dict, ErrorDetail, str]] = None,
        code: t.Optional[t.Union[str, int]] = None,
    ):
        if detail is None:
            detail = str(self.default_detail).format(media_type=media_type)
        super().__init__(detail, code)
