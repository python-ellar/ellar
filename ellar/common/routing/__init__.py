import typing as t

from ellar.core.datastructures import UploadFile
from ellar.core.params import Param, ParamTypes
from ellar.core.routing import OperationDefinitions

from .params import (
    Body,
    Context,
    Cookie,
    File,
    Form,
    Header,
    Host,
    Http,
    Path,
    Provide,
    Query,
    Req,
    Res,
    Session,
    Ws,
    WsBody,
)

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
    "Context",
    "Provide",
    "Req",
    "Ws",
    "Body",
    "WsBody",
    "Cookie",
    "File",
    "UploadFile",
    "Form",
    "Header",
    "Path",
    "Query",
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
    "Res",
    "Session",
    "Host",
    "Http",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
