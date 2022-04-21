import typing as t

from starlette.routing import WebSocketRoute as StarletteWebSocketRoute, compile_path
from starlette.status import WS_1008_POLICY_VIOLATION

from architek.constants import NOT_SET
from architek.core.connection import WebSocket
from architek.core.context import ExecutionContext
from architek.core.endpoints import WebsocketEndpointArgsModel
from architek.core.exceptions import (
    ImproperConfiguration,
    WebSocketRequestValidationError,
)
from architek.core.operation_meta import OperationMeta

from ..base import WebsocketRouteOperationBase
from .handler import WebSocketExtraHandler


class WebSocketOperationMixin:
    _handlers_kwargs: t.Dict

    def connect(self, func: t.Callable[[WebSocket], None]) -> t.Callable:
        self._handlers_kwargs.update(on_connect=func)
        return func

    def disconnect(self, func: t.Callable[[WebSocket, int], None]) -> t.Callable:
        self._handlers_kwargs.update(on_disconnect=func)
        return func

    def custom_handler(self, name: str) -> t.Callable:
        def _wrap(func: t.Callable) -> t.Callable:
            self._handlers_kwargs.update({name: func})
            return func

        return _wrap


class WebsocketRouteOperation(
    WebsocketRouteOperationBase, StarletteWebSocketRoute, WebSocketOperationMixin
):
    websocket_endpoint_args_model: t.Type[
        WebsocketEndpointArgsModel
    ] = WebsocketEndpointArgsModel

    __slots__ = (
        "endpoint",
        "_handlers_kwargs",
        "endpoint_parameter_model",
        "_meta",
        "_extra_handler_type",
    )

    def __init__(
        self,
        *,
        path: str,
        name: t.Optional[str] = None,
        endpoint: t.Callable,
        encoding: str = "json",
        use_extra_handler: bool = False,
        extra_handler_type: t.Optional[t.Type[WebSocketExtraHandler]] = None,
        **handlers_kwargs: t.Any,
    ) -> None:
        self._handlers_kwargs: t.Dict[str, t.Any] = dict(
            encoding=encoding,
            on_receive=None,
            on_connect=None,
            on_disconnect=None,
        )
        self._handlers_kwargs.update(handlers_kwargs)
        self._use_extra_handler = use_extra_handler
        self._extra_handler_type: t.Optional[
            t.Type[WebSocketExtraHandler]
        ] = extra_handler_type

        super().__init__(path=path, endpoint=endpoint, name=name)
        self.endpoint_parameter_model: WebsocketEndpointArgsModel = NOT_SET

        _meta = getattr(self.endpoint, "_meta", {})
        self._meta: OperationMeta = OperationMeta(**_meta)

        if self._use_extra_handler:
            self._handlers_kwargs.update(on_receive=self.endpoint)
        self._load_model()

    @classmethod
    def get_websocket_handler(cls) -> t.Type[WebSocketExtraHandler]:
        return WebSocketExtraHandler

    async def _handle(self, context: ExecutionContext) -> None:
        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            websocket = context.switch_to_websocket()
            exc = WebSocketRequestValidationError(errors)
            await context.switch_to_websocket().send_json(
                dict(code=WS_1008_POLICY_VIOLATION, errors=exc.errors())
            )
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise exc

        if self._use_extra_handler:
            ws_extra_handler_type = (
                self._extra_handler_type or self.get_websocket_handler()
            )
            ws_extra_handler = ws_extra_handler_type(
                route_parameter_model=self.endpoint_parameter_model,
                **self._handlers_kwargs,
            )
            await ws_extra_handler.dispatch(context=context, **func_kwargs)
        else:
            await self.endpoint(**func_kwargs)

    def _load_model(self) -> None:
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )

        self.endpoint_parameter_model = self.websocket_endpoint_args_model(
            path=self.path_format, endpoint=self.endpoint
        )

        if self._meta.extra_route_args:
            self.endpoint_parameter_model.add_extra_route_args(
                *self._meta.extra_route_args
            )
        self.endpoint_parameter_model.build_model()

        if not self._use_extra_handler and self.endpoint_parameter_model.body_resolver:
            raise ImproperConfiguration(
                "`WsBody` should only be used when "
                "`use_extra_handler` flag is set to True in WsRoute"
            )

    def __hash__(self) -> int:
        return hash((self.path, tuple(["ws"])))
