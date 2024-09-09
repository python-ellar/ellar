import typing as t

from ellar.common.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
    EXTRA_ROUTE_ARGS_KEY,
    NOT_SET,
)
from ellar.common.exceptions import (
    ImproperConfiguration,
    WebSocketRequestValidationError,
)
from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import request_logger
from ellar.common.params import ExtraEndpointArg, WebsocketEndpointArgsModel
from ellar.reflect import reflect
from ellar.utils import get_name
from starlette.routing import WebSocketRoute as StarletteWebSocketRoute
from starlette.routing import compile_path
from starlette.status import WS_1008_POLICY_VIOLATION
from starlette.websockets import WebSocketState

from ..base import WebsocketRouteOperationBase
from .handler import WebSocketExtraHandler


class WebsocketRouteOperation(WebsocketRouteOperationBase, StarletteWebSocketRoute):
    websocket_endpoint_args_model: t.Type[WebsocketEndpointArgsModel] = (
        WebsocketEndpointArgsModel
    )

    __slots__ = (
        "endpoint",
        "_handlers_kwargs",
        "endpoint_parameter_model",
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
        super().__init__(endpoint=endpoint)
        assert path.startswith("/"), "Routed paths must start with '/'"
        self._handlers_kwargs: t.Dict[str, t.Any] = {
            "encoding": encoding,
            "on_receive": None,
            "on_connect": None,
            "on_disconnect": None,
        }
        self._handlers_kwargs.update(handlers_kwargs)
        self._use_extra_handler = use_extra_handler
        self._extra_handler_type: t.Optional[t.Type[WebSocketExtraHandler]] = (
            extra_handler_type
        )

        self.path = path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )
        self.name = get_name(endpoint) if name is None else name

        self.endpoint_parameter_model: WebsocketEndpointArgsModel = NOT_SET

        reflect.define_metadata(CONTROLLER_OPERATION_HANDLER_KEY, self, self.endpoint)

        if self._use_extra_handler:
            self._handlers_kwargs.update(on_receive=self.endpoint)
        self._load_model()

    @classmethod
    def get_websocket_handler(cls) -> t.Type[WebSocketExtraHandler]:
        return WebSocketExtraHandler

    def add_websocket_handler(self, handler_name: str, handler: t.Callable) -> None:
        if handler_name not in self._handlers_kwargs:
            raise Exception(
                f"Invalid Handler Name. Handler Name must be in {list(self._handlers_kwargs.keys())}"
            )
        self._handlers_kwargs.update({handler_name: handler})

    async def run(self, context: IExecutionContext, kwargs: t.Dict) -> t.Any:
        request_logger.debug(
            f"Running Websocket Endpoint handler from '{self.__class__.__name__}'"
        )
        if self._use_extra_handler:
            request_logger.debug(
                f"Switched Websocket Extra Handler from '{self.__class__.__name__}'"
            )
            ws_extra_handler_type = (
                self._extra_handler_type or self.get_websocket_handler()
            )
            ws_extra_handler = ws_extra_handler_type(
                route_parameter_model=self.endpoint_parameter_model,
                **self._handlers_kwargs,
            )
            return await ws_extra_handler.dispatch(context=context, **kwargs)
        else:
            return await self.endpoint(**kwargs)

    async def handle_request(self, context: IExecutionContext) -> t.Any:
        request_logger.debug(
            f"Resolving request handler dependencies '{self.__class__.__name__}'"
        )
        res = await self.endpoint_parameter_model.resolve_dependencies(ctx=context)
        if res.errors:
            websocket = context.switch_to_websocket().get_client()
            exc = WebSocketRequestValidationError(res.errors)
            if websocket.client_state == WebSocketState.CONNECTING:
                await websocket.accept()
            await websocket.send_json(
                {"code": WS_1008_POLICY_VIOLATION, "errors": exc.errors()}
            )
            await websocket.close(code=WS_1008_POLICY_VIOLATION)
            raise exc

        return await self.run(context, res.data)

    async def handle_response(
        self, context: IExecutionContext, response_obj: t.Any
    ) -> None:
        """Websocket has no response"""

    def _load_model(self) -> None:
        extra_route_args: t.List["ExtraEndpointArg"] = (
            reflect.get_metadata(EXTRA_ROUTE_ARGS_KEY, self.endpoint) or []
        )

        if self.endpoint_parameter_model is NOT_SET:
            self.endpoint_parameter_model = self.websocket_endpoint_args_model(
                path=self.path_format,
                endpoint=self.endpoint,
                param_converters=self.param_convertors,
                extra_endpoint_args=extra_route_args,
            )
            self.endpoint_parameter_model.build_model()
        if not self._use_extra_handler and self.endpoint_parameter_model.body_resolver:
            raise ImproperConfiguration(
                "`WsBody` should only be used when "
                "`use_extra_handler` flag is set to True in WsRoute"
            )
