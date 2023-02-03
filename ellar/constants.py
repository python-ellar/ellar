import contextvars
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, no_type_check

from pydantic.fields import (
    SHAPE_LIST,
    SHAPE_SEQUENCE,
    SHAPE_SET,
    SHAPE_TUPLE,
    SHAPE_TUPLE_ELLIPSIS,
)

from .asgi_args import RequestScopeContext

SCOPED_CONTEXT_VAR: contextvars.ContextVar[
    Optional[RequestScopeContext]
] = contextvars.ContextVar("SCOPED-CONTEXT-VAR")
SCOPED_CONTEXT_VAR.set(None)


class _AnnotationToValue(type):
    keys: List[str]

    @no_type_check
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        annotations = dict()
        for base in reversed(bases):  # pragma: no cover
            annotations.update(getattr(base, "__annotations__", {}))
        annotations.update(namespace.get("__annotations__", {}))
        cls.keys = []
        for k, v in annotations.items():
            if type(v) == type(str):
                value = str(k).lower()
                setattr(cls, k, value)
                cls.keys.append(value)
        return cls


POST = "POST"
PUT = "PUT"
PATCH = "PATCH"
DELETE = "DELETE"
GET = "GET"
HEAD = "HEAD"
OPTIONS = "OPTIONS"
TRACE = "TRACE"
ROUTE_METHODS = [POST, PUT, PATCH, DELETE, GET, HEAD, OPTIONS, TRACE]

SCOPE_SERVICE_PROVIDER = "SERVICE_PROVIDER"
SCOPE_RESPONSE_STARTED = "__response_started__"
SCOPED_RESPONSE = "__response__"
SCOPE_API_VERSIONING_RESOLVER = "API_VERSIONING_RESOLVER"
SCOPE_API_VERSIONING_SCHEME = "API_VERSIONING_SCHEME"
ELLAR_CONFIG_MODULE = "ELLAR_CONFIG_MODULE"
INJECTABLE_ATTRIBUTE = "__DI_SCOPE__"

SERIALIZER_FILTER_KEY = "SERIALIZER_FILTER"
OPENAPI_KEY = "OPENAPI"
VERSIONING_KEY = "ROUTE_VERSIONING"
GUARDS_KEY = "ROUTE_GUARDS"
EXTRA_ROUTE_ARGS_KEY = "EXTRA_ROUTE_ARGS"
RESPONSE_OVERRIDE_KEY = "RESPONSE_OVERRIDE"
EXCEPTION_HANDLERS_KEY = "EXCEPTION_HANDLERS"

ON_REQUEST_STARTUP_KEY = "ON_REQUEST_STARTUP"
ON_REQUEST_SHUTDOWN_KEY = "ON_REQUEST_SHUTDOWN"

TEMPLATE_GLOBAL_KEY = "TEMPLATE_GLOBAL_FILTERS"
TEMPLATE_FILTER_KEY = "TEMPLATE_FILTERS"

MIDDLEWARE_HANDLERS_KEY = "MIDDLEWARE"

MODULE_WATERMARK = "MODULE_WATERMARK"
MODULE_FIELDS = "__MODULE_FIELDS__"
CONTROLLER_WATERMARK = "CONTROLLER_WATERMARK"

MULTI_RESOLVER_KEY = "MULTI_RESOLVER_KEY"
MULTI_RESOLVER_FORM_GROUPED_KEY = "MULTI_RESOLVER_FORM_GROUPED_KEY"
ROUTE_OPENAPI_PARAMETERS = "ROUTE_OPENAPI_PARAMETERS"

OPERATION_ENDPOINT_KEY = "OPERATION_ENDPOINT"
CONTROLLER_OPERATION_HANDLER_KEY = "CONTROLLER_OPERATION_HANDLER"
CONTROLLER_CLASS_KEY = "CONTROLLER_CLASS_KEY"
REFLECT_TYPE = "__REFLECT_TYPE__"
CALLABLE_COMMAND_INFO = "__CALLABLE_COMMAND_INFO__"
GROUP_METADATA = "GROUP_METADATA"
ELLAR_META = "ELLAR_META"
ELLAR_PY_PROJECT = "ellar"


class MODULE_REF_TYPES(metaclass=_AnnotationToValue):
    PLAIN: str
    TEMPLATE: str


class MODULE_METADATA(metaclass=_AnnotationToValue):
    NAME: str
    CONTROLLERS: str
    BASE_DIRECTORY: str
    STATIC_FOLDER: str
    ROUTERS: str
    PROVIDERS: str
    TEMPLATE_FOLDER: str
    MODULES: str
    COMMANDS: str


class CONTROLLER_METADATA(metaclass=_AnnotationToValue):
    OPENAPI: str
    PATH: str
    NAME: str
    INCLUDE_IN_SCHEMA: str


sequence_shapes = {
    SHAPE_LIST,
    SHAPE_SET,
    SHAPE_TUPLE,
    SHAPE_SEQUENCE,
    SHAPE_TUPLE_ELLIPSIS,
}
sequence_types = (list, set, tuple)
sequence_shape_to_type = {
    SHAPE_LIST: list,
    SHAPE_SET: set,
    SHAPE_TUPLE: tuple,
    SHAPE_SEQUENCE: list,
    SHAPE_TUPLE_ELLIPSIS: list,
}
primitive_types = (int, float, bool, str)
METHODS_WITH_BODY = {"GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"}
STATUS_CODES_WITH_NO_BODY = {100, 101, 102, 103, 204, 304}
REF_PREFIX = "#/components/schemas/"
ELLAR_TRACE_LOG_LEVEL = 5


class LOG_LEVELS(Enum):
    critical = logging.CRITICAL
    error = logging.ERROR
    warning = logging.WARNING
    info = logging.INFO
    debug = logging.DEBUG
    trace = ELLAR_TRACE_LOG_LEVEL


class NOT_SET_TYPE:
    def __repr__(self) -> str:  # pragma: no cover
        return f"{__name__}.{self.__class__.__name__}"

    def __copy__(self) -> Any:  # pragma: no cover
        return NOT_SET

    def __deepcopy__(self, memodict: Dict = {}) -> Any:  # pragma: no cover
        return NOT_SET


NOT_SET: Any = NOT_SET_TYPE()


DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        "ellar": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
