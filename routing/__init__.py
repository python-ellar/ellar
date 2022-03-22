from starlette.routing import ( # noqa
    BaseRoute,
    Route as StarletteRoute,
    WebSocketRoute,
    Match,
    NoMatchFound,
    iscoroutinefunction_or_partial
)
from .base import ModuleRouter, AppRouter, AppRoutes # noqa
from starletteapi.route_models.params import Header, Query, Cookie, Body, File, Form, Path # noqa
from .route_definitions import RouteDefinitions
from .decorator import SetMeta, Guards, Versions

_route_definitions = RouteDefinitions()

Get = _route_definitions.Get
Post = _route_definitions.Post

Delete = _route_definitions.Delete
Patch = _route_definitions.Patch

Put = _route_definitions.Put
Options = _route_definitions.Options

Trace = _route_definitions.Trace
Head = _route_definitions.Head

HttpRoute = _route_definitions.HttpRoute
WsRoute = _route_definitions.WsRoute
