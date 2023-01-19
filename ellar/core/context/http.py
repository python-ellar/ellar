import typing as t

from starlette.background import BackgroundTasks
from starlette.responses import Response

from ellar.compatible import cached_property
from ellar.constants import SCOPED_RESPONSE
from ellar.core.connection import HTTPConnection, Request
from ellar.types import TReceive, TScope, TSend

from .exceptions import HostContextException
from .interface import IHTTPHostContext


class HTTPHostContext(IHTTPHostContext):
    """
    Provides a context around HTTP Connection
    """

    __slots__ = (
        "scope",
        "receive",
        "send",
        "_response",
    )

    def __init__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send
        self._response: t.Optional[Response] = None

    @cached_property
    def _http_connection(self) -> HTTPConnection:
        return HTTPConnection(scope=self.scope, receive=self.receive)

    @cached_property
    def _request(self) -> Request:
        if self.scope["type"] != "http":
            raise HostContextException(
                f"Request Context is not allow for scope[type]={self.scope['type']}"
            )
        return Request(scope=self.scope, receive=self.receive, send=self.send)

    @property
    def has_response(self) -> bool:
        return SCOPED_RESPONSE in self.scope

    def get_response(self) -> Response:
        if SCOPED_RESPONSE not in self.scope:
            if self.scope["type"] != "http":
                raise HostContextException(
                    f"Response is not allow for connection type scope[type]={self.scope['type']}"
                )

            self.scope[SCOPED_RESPONSE] = Response(
                background=BackgroundTasks(),
                content=None,
                status_code=-100,
            )

        return t.cast(Response, self.scope[SCOPED_RESPONSE])

    def get_request(self) -> Request:
        return self._request  # type: ignore

    def get_client(self) -> HTTPConnection:
        return self._http_connection  # type: ignore
