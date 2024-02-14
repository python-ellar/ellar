from .base import OperationDefinitions
from .router import ModuleRouter
from .schema import RouteParameters, TResponseModel, WsRouteParameters

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
    "RouteParameters",
    "TResponseModel",
    "WsRouteParameters",
    "ModuleRouter",
    "OperationDefinitions",
]
