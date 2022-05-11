import typing as t

from ellar.core.context import ExecutionContext
from ellar.core.operation_meta import OperationMeta

from .model import ControllerBase


class ControllerRouteOperationBase:
    _meta: OperationMeta

    endpoint: t.Callable

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super(ControllerRouteOperationBase, self).__init__(*args, **kwargs)
        self._controller_type: t.Optional[t.Type[ControllerBase]] = None

    @property
    def controller_type(self) -> t.Type[ControllerBase]:
        if self._controller_type:
            return self._controller_type
        raise Exception("Controller Type found")

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
