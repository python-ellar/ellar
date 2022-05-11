from typing import Any, Dict

from pydantic.fields import (
    SHAPE_LIST,
    SHAPE_SEQUENCE,
    SHAPE_SET,
    SHAPE_TUPLE,
    SHAPE_TUPLE_ELLIPSIS,
)

POST = "POST"
PUT = "PUT"
PATCH = "PATCH"
DELETE = "DELETE"
GET = "GET"
HEAD = "HEAD"
OPTIONS = "OPTIONS"
TRACE = "TRACE"
ROUTE_METHODS = [POST, PUT, PATCH, DELETE, GET, HEAD, OPTIONS, TRACE]

SCOPE_SERVICE_PROVIDER = "service_provider"
SCOPE_API_VERSIONING_RESOLVER = "api_versioning_resolver"
SCOPE_API_VERSIONING_SCHEME = "api_versioning_scheme"
ELLAR_CONFIG_MODULE = "ELLAR_CONFIG_MODULE"
INJECTABLE_ATTRIBUTE = "__di_scope__"

SERIALIZER_FILTER_KEY = "serializer_filter"
OPENAPI_KEY = "openapi"
VERSIONING_KEY = "route_versioning"
GUARDS_KEY = "route_guards"
EXTRA_ROUTE_ARGS_KEY = "extra_route_args"
RESPONSE_OVERRIDE_KEY = "response_override"
EXCEPTION_HANDLERS_KEY = "__EXCEPTION_HANDLERS_DECORATOR__"
ON_STARTUP_KEY = "__ON_STARTUP_KEY__"
ON_SHUTDOWN_KEY = "__ON_SHUTDOWN_KEY__"
ON_APP_STARTED = "__ON_APP_STARTED__"
ON_APP_INIT = "__ON_APP_INIT__"
MIDDLEWARE_HANDLERS_KEY = "__MIDDLEWARE_DECORATOR__"
APP_MODULE_KEY = "APP_MODULE_KEY"

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


class _NOT_SET:
    def __copy__(self) -> Any:
        return NOT_SET

    def __deepcopy__(self, memodict: Dict = {}) -> Any:
        return NOT_SET


NOT_SET: Any = _NOT_SET()
