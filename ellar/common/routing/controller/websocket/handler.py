import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.logger import request_logger
from ellar.common.models import ControllerBase

from ...websocket import WebSocketExtraHandler


class ControllerWebSocketExtraHandler(WebSocketExtraHandler):
    def __init__(self, controller_instance: ControllerBase, **kwargs: t.Any):
        super().__init__(**kwargs)
        self.controller_instance = controller_instance

    async def execute_on_receive(
        self, *, context: IExecutionContext, data: t.Any, **receiver_kwargs: t.Any
    ) -> None:
        extra_kwargs = await self._resolve_receiver_dependencies(
            context=context, data=data
        )

        receiver_kwargs.update(extra_kwargs)
        request_logger.debug(
            f"Executing on_receive handler from {self.__class__.__name__}"
        )
        await self.on_receive(self.controller_instance, **receiver_kwargs)

    async def execute_on_connect(self, *, context: IExecutionContext) -> None:
        if self.on_connect:
            request_logger.debug(
                f"Executing on_connect handler from {self.__class__.__name__}"
            )
            await self.on_connect(
                self.controller_instance, context.switch_to_websocket().get_client()
            )
            return
        await context.switch_to_websocket().get_client().accept()

    async def execute_on_disconnect(
        self, *, context: IExecutionContext, close_code: int
    ) -> None:
        if self.on_disconnect:
            request_logger.debug(
                f"Executing on_disconnect handler from {self.__class__.__name__}"
            )
            await self.on_disconnect(
                self.controller_instance,
                context.switch_to_websocket().get_client(),
                close_code,
            )
