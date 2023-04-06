from starlette.exceptions import HTTPException, WebSocketException

from .base import APIException
from .exceptions_types import (
    AuthenticationFailed,
    ImproperConfiguration,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    UnsupportedMediaType,
)
from .interfaces import IExceptionHandler, IExceptionMiddlewareService
from .validation import RequestValidationError, WebSocketRequestValidationError

__all__ = [
    "IExceptionHandler",
    "IExceptionMiddlewareService",
    "HTTPException",
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
    "WebSocketException",
]
