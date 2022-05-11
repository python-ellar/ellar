import typing as t

from starlette.concurrency import run_in_threadpool

from ellar.core.context import ExecutionContext
from ellar.core.routing.route import RouteOperation
from ellar.exceptions import ImproperConfiguration, RequestValidationError

from .base import ControllerRouteOperationBase
from .model import ControllerBase


class ControllerRouteOperation(ControllerRouteOperationBase, RouteOperation):
    def build_route_operation(  # type:ignore
        self,
        path_prefix: str = "/",
        name: t.Optional[str] = None,
        include_in_schema: bool = True,
        controller_type: t.Optional[t.Type[ControllerBase]] = None,
        **kwargs: t.Any
    ) -> None:
        if name and not controller_type:
            raise ImproperConfiguration(
                "`controller_type` is required for Controller Route Operation"
            )
        self._controller_type = controller_type
        self._meta.update(controller_type=controller_type)
        super().build_route_operation(
            path_prefix=path_prefix, name=name, include_in_schema=include_in_schema
        )

    async def _handle_request(self, context: ExecutionContext) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)

        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            raise RequestValidationError(errors)

        if self._is_coroutine:
            response_obj = await self.endpoint(controller_instance, **func_kwargs)
        else:
            response_obj = await run_in_threadpool(
                self.endpoint, controller_instance, **func_kwargs
            )
        response = self.response_model.process_response(
            ctx=context, response_obj=response_obj
        )
        await response(context.scope, context.receive, context.send)
