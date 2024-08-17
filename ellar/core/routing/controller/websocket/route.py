import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import request_logger

from ...websocket import WebsocketRouteOperation
from ..base import ControllerRouteOperationBase
from .handler import ControllerWebSocketExtraHandler


class ControllerWebsocketRouteOperation(
    ControllerRouteOperationBase, WebsocketRouteOperation
):
    _extra_handler_type: t.Optional[t.Type[ControllerWebSocketExtraHandler]]

    @property
    def router_reflect_key(self) -> t.Any:
        return self.controller

    @classmethod
    def get_websocket_handler(cls) -> t.Type[ControllerWebSocketExtraHandler]:
        return ControllerWebSocketExtraHandler

    async def run(self, context: IExecutionContext, kwargs: t.Dict) -> t.Any:
        request_logger.debug(
            f"Running Websocket Endpoint handler from '{self.__class__.__name__}'"
        )
        controller_instance = self._get_controller_instance(ctx=context)
        if self._use_extra_handler:
            request_logger.debug(
                f"Switched Websocket Extra Handler from '{self.__class__.__name__}'"
            )
            ws_extra_handler_type = (
                self._extra_handler_type or self.get_websocket_handler()
            )
            ws_extra_handler = ws_extra_handler_type(
                route_parameter_model=self.endpoint_parameter_model,
                controller_instance=controller_instance,
                **self._handlers_kwargs,
            )
            return await ws_extra_handler.dispatch(context=context, **kwargs)
        else:
            return await self.endpoint(controller_instance, **kwargs)
