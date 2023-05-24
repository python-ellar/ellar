import typing as t

from starlette.concurrency import run_in_threadpool

from ellar.common.exceptions import RequestValidationError
from ellar.common.interfaces import IExecutionContext
from ellar.common.routing.route import RouteOperation

from .base import ControllerRouteOperationBase


class ControllerRouteOperation(ControllerRouteOperationBase, RouteOperation):
    methods: t.Set[str]

    async def handle_request(self, context: IExecutionContext) -> t.Any:
        controller_instance = self._get_controller_instance(ctx=context)

        func_kwargs, errors = await self.endpoint_parameter_model.resolve_dependencies(
            ctx=context
        )
        if errors:
            raise RequestValidationError(errors)

        if self._is_coroutine:
            return await self.endpoint(controller_instance, **func_kwargs)
        else:
            return await run_in_threadpool(
                self.endpoint, controller_instance, **func_kwargs
            )
