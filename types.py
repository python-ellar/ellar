import typing as t
from starlette.types import Scope as TScope, Receive as TReceive, Send as TSend, ASGIApp, Message  # noqa
from starletteapi.requests import Request
from starletteapi.websockets import WebSocket

TRequest = t.Union[Request, WebSocket]
TemplateFilterCallable = t.Callable[..., t.Any]
TemplateGlobalCallable = t.Callable[..., t.Any]
T = t.TypeVar('T')
KT = t.TypeVar('KT')
VT = t.TypeVar('VT')
