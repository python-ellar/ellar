import functools
import typing as t

from ellar.common import EllarInterceptor, IExecutionContext, InterceptorConsumer
from ellar.common.constants import ROUTE_INTERCEPTORS, SCOPE_RESPONSE_STARTED
from ellar.di import injectable

from ..services import Reflector

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common.routing import RouteOperationBase


@injectable
class EllarInterceptorConsumer(InterceptorConsumer):
    def __init__(self, reflector: Reflector) -> None:
        self.reflector = reflector

    def get_interceptor(
        self,
        context: IExecutionContext,
        interceptor: t.Union[t.Type[EllarInterceptor], EllarInterceptor],
    ) -> EllarInterceptor:
        if isinstance(interceptor, type):
            return t.cast(
                EllarInterceptor, context.get_service_provider().get(interceptor)
            )
        return interceptor

    async def execute(
        self, context: IExecutionContext, route_operation: "RouteOperationBase"
    ) -> t.Any:
        interceptor_idx = 0
        route_interceptors: t.List = (
            self.reflector.get_all_and_override(  # type:ignore[assignment]
                ROUTE_INTERCEPTORS, *[context.get_handler(), context.get_class()]
            )
        )
        route_interceptors_length = len(route_interceptors or [])

        if route_interceptors:
            route_interceptors = [
                self.get_interceptor(context, item) for item in route_interceptors
            ]

            async def handler(idx: int) -> t.Any:
                if idx >= route_interceptors_length:
                    return await route_operation.handle_request(context=context)
                return await route_interceptors[idx].intercept(
                    context, functools.partial(handler, interceptor_idx + 1)
                )

            res = await handler(0)
        else:
            res = await route_operation.handle_request(context=context)

        if context.get_args()[0][SCOPE_RESPONSE_STARTED]:
            print("\nResponse Started")
            return
        await route_operation.handle_response(context, res)
