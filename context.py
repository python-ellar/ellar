import email
import json
from typing import TYPE_CHECKING, cast, Optional, Any

from pydantic.error_wrappers import ErrorWrapper
from pydantic.fields import Undefined
from starlette.background import BackgroundTasks

from starlette.exceptions import HTTPException
from starletteapi.requests import Request, HTTPConnection
from starletteapi.responses import Response
from starletteapi.types import TScope, TReceive, TSend
from starletteapi.websockets import WebSocket
from .exceptions import RequestValidationError

from .helper import cached_property

if TYPE_CHECKING:
    from starletteapi.main import StarletteApp
    from starletteapi.di.injector import DIRequestServiceProvider
    from starletteapi.routing.operations import OperationBase


class ExecutionContextException(Exception):
    pass


class ExecutionContext:
    def __init__(self, *, scope: TScope, receive: TReceive, send: TSend, operation: 'OperationBase'):
        self.scope = scope
        self.receive = receive
        self.send = send
        self._operation = operation
        self._request_body: Optional[Any] = None
        self._request_form: Optional[Any] = None

    @property
    def operation(self):
        return self._operation

    @property
    def has_response(self) -> bool:
        return self._response is not None

    @cached_property
    def _response(self):
        return Response(background=BackgroundTasks())

    @cached_property
    def _service_provider(self) -> Optional['DIRequestServiceProvider']:
        service_provider = self.scope.get('service_provider')
        if not service_provider:
            service_provider = self.get_app().injector.create_di_request_service_provider(
                {ExecutionContext: self}
            )
        if ExecutionContext not in service_provider.context:
            service_provider.update_context(ExecutionContext, self)
        return service_provider

    @cached_property
    def _http_connection(self) -> HTTPConnection:
        return HTTPConnection(self.scope, receive=self.receive)

    @cached_property
    def _request(self) -> Request:
        if self.scope['type'] != 'http':
            raise ExecutionContextException(f"Context Switch is not allow for scope[type]={self.scope['type']}")
        return Request(self.scope, receive=self.receive, send=self.send)

    @cached_property
    def _websocket(self) -> WebSocket:
        if self.scope['type'] != 'websocket':
            raise ExecutionContextException(f"Context Switch is not allow for scope[type]={self.scope['type']}")
        return WebSocket(self.scope, receive=self.receive, send=self.send)

    async def get_request_body(self) -> Any:
        if not self._request_body:
            try:
                request = self.switch_to_request()
                body_bytes = await request.body()
                if body_bytes:
                    json_body: Any = Undefined
                    content_type_value = request.headers.get("content-type")
                    if not content_type_value:
                        json_body = await request.json()
                    else:
                        message = email.message.Message()
                        message["content-type"] = content_type_value
                        if message.get_content_maintype() == "application":
                            subtype = message.get_content_subtype()
                            if subtype == "json" or subtype.endswith("+json"):
                                json_body = await request.json()
                    if json_body != Undefined:
                        body = json_body
                    else:
                        body = body_bytes
                    self._request_body = body
            except json.JSONDecodeError as e:
                raise RequestValidationError([ErrorWrapper(e, ("body", e.pos))])
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail="There was an error parsing the body"
                ) from e
        return self._request_body

    async def get_request_form(self) -> Any:
        if not self._request_form:
            try:
                request = self.switch_to_request()
                body_bytes = await request.form()
                self._request_form = body_bytes
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail="There was an error parsing the body"
                ) from e
        return self._request_form

    def get_service_provider(self) -> "DIRequestServiceProvider":
        return self._service_provider

    def switch_to_request(self) -> Request:
        return self._request

    def switch_to_http_connection(self) -> HTTPConnection:
        return self._http_connection

    def switch_to_websocket(self) -> WebSocket:
        return self._websocket

    def get_response(self) -> Response:
        return self._response

    def get_app(self) -> 'StarletteApp':
        return cast('StarletteApp', self.scope["app"])
