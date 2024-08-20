import logging
import typing as t
from enum import Enum
from typing import Any

from ellar.common.types import TMessage
from ellar.di import AnnotationToValue

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


SERIALIZER_FILTER_KEY = "SERIALIZER_FILTER"
VERSIONING_KEY = "ROUTE_VERSIONING"
GUARDS_KEY = "ROUTE_GUARDS"
EXTRA_ROUTE_ARGS_KEY = "EXTRA_ROUTE_ARGS"
RESPONSE_OVERRIDE_KEY = "RESPONSE_OVERRIDE"
EXCEPTION_HANDLERS_KEY = "EXCEPTION_HANDLERS"
APP_EXCEPTION_HANDLERS_KEY = "APP_EXCEPTION_HANDLERS"
MODULE_DECORATOR_ITEM = "MODULE_DECORATOR_ITEM"
TEMPLATE_GLOBAL_KEY = "TEMPLATE_GLOBAL_FILTERS"
TEMPLATE_CONTEXT_PROCESSOR_KEY = "TEMPLATE_CONTEXT_PROCESSOR_KEY"
TEMPLATE_FILTER_KEY = "TEMPLATE_FILTERS"
NESTED_ROUTERS_KEY = "NESTED_ROUTERS_KEY"
ROUTER_PRE_BUILD_ROUTES = "PRE_BUILD_ROUTES"

MIDDLEWARE_HANDLERS_KEY = "MIDDLEWARE"
APP_MIDDLEWARE_HANDLERS_KEY = "APP_MIDDLEWARE"

MODULE_WATERMARK = "MODULE_WATERMARK"
CONTROLLER_WATERMARK = "CONTROLLER_WATERMARK"

MULTI_RESOLVER_KEY = "MULTI_RESOLVER_KEY"
MULTI_RESOLVER_FORM_GROUPED_KEY = "MULTI_RESOLVER_FORM_GROUPED_KEY"
ROUTE_OPENAPI_PARAMETERS = "ROUTE_OPENAPI_PARAMETERS"

OPERATION_ENDPOINT_KEY = "OPERATION_ENDPOINT"
ROUTE_OPERATION_PARAMETERS = "__ROUTE_OPERATION_PARAMETERS__"
ROUTE_INTERCEPTORS = "ROUTE_INTERCEPTORS"
ROUTE_CACHE_OPTIONS = "ROUTE_CACHE_OPTIONS"
CONTROLLER_OPERATION_HANDLER_KEY = "CONTROLLER_OPERATION_HANDLER"
CONTROLLER_CLASS_KEY = "CONTROLLER_CLASS_KEY"

GROUP_METADATA = "GROUP_METADATA"
SKIP_AUTH = "SKIP_AUTH"
MODULE_COMPONENT = "MODULE_COMPONENT"


class MODULE_METADATA(metaclass=AnnotationToValue):
    NAME: str
    CONTROLLERS: str
    BASE_DIRECTORY: str
    STATIC_FOLDER: str
    ROUTERS: str
    PROVIDERS: str
    TEMPLATE_FOLDER: str
    MODULES: str
    COMMANDS: str
    EXPORTS: str


class CONTROLLER_METADATA(metaclass=AnnotationToValue):
    PATH: str
    NAME: str
    INCLUDE_IN_SCHEMA: str
    PROCESSED: str
    MIDDLEWARE: str


sequence_types = (list, set, tuple)

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

    def __deepcopy__(
        self, memodict: t.Optional[t.Any] = None
    ) -> Any:  # pragma: no cover
        if memodict is None:
            memodict = {}
        return NOT_SET


NOT_SET: Any = NOT_SET_TYPE()

ELLAR_LOG_FMT_STRING = "%(levelname)s: [%(name)s] %(message)s"
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
        "ellar-formatter": {
            "()": "logging.Formatter",
            "fmt": ELLAR_LOG_FMT_STRING,
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
        "ellar-default": {
            "formatter": "ellar-formatter",
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
            "handlers": ["ellar-default"],
            "level": "INFO",
            "propagate": False,
        },
        "ellar.request": {
            "handlers": ["ellar-default"],
            "level": "INFO",
            "propagate": False,
        },
        "ellar.di": {
            "handlers": ["ellar-default"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


async def empty_receive() -> t.NoReturn:  # pragma: no cover
    raise RuntimeError("Receive channel has not been made available")


async def empty_send(message: TMessage) -> t.NoReturn:  # pragma: no cover
    raise RuntimeError("Send channel has not been made available")
