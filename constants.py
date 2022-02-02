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


class _NOT_SET:
    def __copy__(self) -> Any:
        return NOT_SET

    def __deepcopy__(self, memodict: Dict = {}) -> Any:
        return NOT_SET


NOT_SET: Any = _NOT_SET()
