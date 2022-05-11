import typing as t

from starlette.status import WS_1008_POLICY_VIOLATION

from ellar.core.context import ExecutionContext
from ellar.exceptions import ImproperConfiguration, WebSocketRequestValidationError

from ...websocket import WebsocketRouteOperation
from ..base import ControllerRouteOperationBase
from ..model import ControllerBase
from .handler import ControllerWebSocketExtraHandler


class ControllerWebsocketRouteOperation(
    ControllerRouteOperationBase, WebsocketRouteOperation
):
    _extra_handler_type: t.Optional[t.Type[ControllerWebSocketExtraHandler]]

    def build_route_operation(  # type:ignore
        self,
        path_prefix: str = "",
        name: t.Optional[str] = None,
        controller_type: t.Optional[t.Type[ControllerBase]] = None,
        **kwargs: t.Any
    ) -> None:
        if name and not controller_type:
            raise ImproperConfiguration(
                "`controller_type` is required for Controller Route Operation"
            )
        self._controller_type = controller_type
        self._meta.update(controller_type=controller_type)
        super().build_route_operation(path_prefix=path_prefix, name=name)

    @classmethod
    def get_websocket_handler(cls) -> t.Type[ControllerWebSocketExtraHandler]:
        return ControllerWebSocketExtraHandler

    async def _handle_request(self, context: ExecutionContext) -> None:
        controller_instance = self._get_controller_instance(ctx=context)
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
                controller_instance=controller_instance,
                **self._handlers_kwargs,
            )
            await ws_extra_handler.dispatch(context=context, **func_kwargs)
        else:
            await self.endpoint(controller_instance, **func_kwargs)
