from starlette.routing import (
    BaseRoute,
    Match,
    NoMatchFound,
    Route as StarletteRoute,
    WebSocketRoute as StarletteWebSocketRoute,
    iscoroutinefunction_or_partial,
)

from architek.route_models.params import Body, Cookie, File, Form, Header, Path, Query

from .base import AppRouter, AppRoutes, ModuleRouter
from .decorator import guards, set_meta, version
from .route_definitions import RouteDefinitions

_route_definitions = RouteDefinitions()

Get = _route_definitions.get
Post = _route_definitions.post

Delete = _route_definitions.delete
Patch = _route_definitions.patch

Put = _route_definitions.put
Options = _route_definitions.options

Trace = _route_definitions.trace
Head = _route_definitions.head

HttpRoute = _route_definitions.http_route
WsRoute = _route_definitions.ws_route

__all__ = [
    "set_meta",
    "version",
    "guards",
    "AppRouter",
    "AppRoutes",
    "ModuleRouter",
    "Body",
    "Cookie",
    "File",
    "Form",
    "Header",
    "Path",
    "Query",
    "StarletteWebSocketRoute",
    "StarletteRoute",
    "iscoroutinefunction_or_partial",
    "NoMatchFound",
    "Match",
    "BaseRoute",
    "RouteDefinitions",
    "Get",
    "Post",
    "Delete",
    "Patch",
    "Put",
    "Options",
    "Trace",
    "Head",
    "HttpRoute",
    "WsRoute",
]
