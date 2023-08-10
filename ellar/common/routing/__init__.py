import typing as t

from ellar.common.params.params import ParamFieldInfo as Param
from ellar.common.params.params import ParamTypes
from starlette.routing import Host, Mount

from .base import RouteOperationBase
from .mount import ModuleMount, ModuleRouter
from .operation_definitions import OperationDefinitions
from .route import RouteOperation
from .route_collections import RouteCollection
from .websocket import WebsocketRouteOperation

_route_definitions = OperationDefinitions()

get = _route_definitions.get
post = _route_definitions.post

delete = _route_definitions.delete
patch = _route_definitions.patch

put = _route_definitions.put
options = _route_definitions.options

trace = _route_definitions.trace
head = _route_definitions.head

http_route = _route_definitions.http_route
ws_route = _route_definitions.ws_route

__all__ = [
    "Param",
    "ParamTypes",
    "get",
    "post",
    "delete",
    "patch",
    "put",
    "options",
    "trace",
    "head",
    "http_route",
    "ws_route",
    "RouteCollection",
    "ModuleRouter",
    "ModuleMount",
    "RouteOperation",
    "RouteOperationBase",
    "OperationDefinitions",
    "WebsocketRouteOperation",
    "Host",
    "Mount",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
