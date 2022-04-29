from ellar.core.params import Param, ParamTypes
from ellar.core.routing import OperationDefinitions

from .params import (
    Body,
    Cookie,
    Ctx,
    File,
    Form,
    Header,
    Path,
    Provide,
    Query,
    Req,
    Ws,
    WsBody,
)

_route_definitions = OperationDefinitions()

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
    "Ctx",
    "Provide",
    "Req",
    "Ws",
    "Body",
    "WsBody",
    "Cookie",
    "File",
    "Form",
    "Header",
    "Path",
    "Query",
    "Param",
    "ParamTypes",
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
