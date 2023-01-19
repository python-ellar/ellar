import typing as t

from starlette.status import WS_1008_POLICY_VIOLATION
from starlette.websockets import WebSocketState

from ellar.core.context import IExecutionContext
from ellar.core.exceptions import WebSocketRequestValidationError

from ...websocket import WebsocketRouteOperation
from ..base import ControllerRouteOperationBase
from .handler import ControllerWebSocketExtraHandler


class ControllerWebsocketRouteOperation(
    ControllerRouteOperationBase, WebsocketRouteOperation
):
    _extra_handler_type: t.Optional[t.Type[ControllerWebSocketExtraHandler]]

    @classmethod
    def get_websocket_handler(cls) -> t.Type[ControllerWebSocketExtraHandler]:
        return ControllerWebSocketExtraHandler

    async def _handle_request(self, context: IExecutionContext) -> None:
        controller_instance = self._get_controller_instance(ctx=context)
        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            websocket = context.switch_to_websocket().get_client()
            exc = WebSocketRequestValidationError(errors)
            if websocket.client_state == WebSocketState.CONNECTING:
                await websocket.accept()
            await websocket.send_json(
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
