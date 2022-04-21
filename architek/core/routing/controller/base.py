import typing as t
from abc import ABC

from architek.core.context import ExecutionContext

from ..base import RouteOperationBase
from .model import ControllerBase


class ControllerRouteOperationBase(RouteOperationBase, ABC):
    def __init__(
        self, controller_type: t.Type[ControllerBase], *args: t.Any, **kwargs: t.Any
    ) -> None:
        super(ControllerRouteOperationBase, self).__init__(*args, **kwargs)
        self.controller_type: t.Type[ControllerBase] = controller_type
        self._meta.update(controller_type=controller_type)

    def _get_controller_instance(self, ctx: ExecutionContext) -> ControllerBase:
        service_provider = ctx.get_service_provider()

        controller_instance = service_provider.get(self.controller_type)
        controller_instance.context = ctx
        return controller_instance

    @t.no_type_check
    def __call__(
        self, context: ExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)
        return self.endpoint(controller_instance, *args, **kwargs)
