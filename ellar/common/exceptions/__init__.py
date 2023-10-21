from starlette.exceptions import HTTPException, WebSocketException

from .api import (
    APIException,
    AuthenticationFailed,
    ImproperConfiguration,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    UnsupportedMediaType,
)
from .callable_exceptions import CallableExceptionHandler
from .context import ExecutionContextException, HostContextException
from .validation import RequestValidationError, WebSocketRequestValidationError

__all__ = [
    "HostContextException",
    "ExecutionContextException",
    "HTTPException",
    "WebSocketException",
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
    "CallableExceptionHandler",
]
