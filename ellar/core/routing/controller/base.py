import typing as t

from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import request_logger
from ellar.common.models import ControllerBase


class ControllerRouteOperationBase:
    get_controller_type: t.Callable

    def __init__(
        self, controller: t.Type[ControllerBase], *args: t.Any, **kwargs: t.Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.controller = controller

    def _get_controller_instance(self, ctx: IExecutionContext) -> ControllerBase:
        request_logger.debug("Getting Controller Instance")
        service_provider = ctx.get_service_provider()

        controller_instance: ControllerBase = service_provider.get(self.controller)
        controller_instance.context = ctx
        return controller_instance

    # @t.no_type_check
    # def __call__(
    #     self, context: IExecutionContext, *args: t.Any, **kwargs: t.Any
    # ) -> t.Any:
    #     request_logger.debug("Calling Controller Endpoint manually")
    #     controller_instance = self._get_controller_instance(ctx=context)
    #     return self.endpoint(controller_instance, *args, **kwargs)
