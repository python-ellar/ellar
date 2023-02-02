import typing as t

from ellar.constants import CONTROLLER_CLASS_KEY
from ellar.core.context import IExecutionContext
from ellar.core.controller import ControllerBase
from ellar.reflect import reflect


class ControllerRouteOperationBase:
    endpoint: t.Callable

    def _get_controller_instance(self, ctx: IExecutionContext) -> ControllerBase:
        controller_type: t.Optional[t.Type[ControllerBase]] = reflect.get_metadata(
            CONTROLLER_CLASS_KEY, self.endpoint
        )
        if not controller_type or (
            controller_type and not issubclass(controller_type, ControllerBase)
        ):
            raise RuntimeError("Controller Type was not found")

        service_provider = ctx.get_service_provider()

        controller_instance: ControllerBase = service_provider.get(controller_type)
        controller_instance.context = ctx  # type:ignore
        return controller_instance

    @t.no_type_check
    def __call__(
        self, context: IExecutionContext, *args: t.Any, **kwargs: t.Any
    ) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)
        return self.endpoint(controller_instance, *args, **kwargs)
