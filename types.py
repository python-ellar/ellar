from typing import Union
from starlette.types import Scope as TScope, Receive as TReceive, Send as TSend, ASGIApp  # noqa
from starletteapi.requests import Request
from starletteapi.websockets import WebSocket

TRequest = Union[Request, WebSocket]
