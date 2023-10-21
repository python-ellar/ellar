import typing as t

from ellar.common.interfaces import IHostContext, IHostContextFactory
from ellar.common.types import ASGIApp, TReceive, TScope, TSend
from ellar.core.connection import HTTPConnection
from starlette.responses import Response

AwaitableCallable = t.Callable[..., t.Awaitable]
DispatchFunction = t.Callable[
    [IHostContext, AwaitableCallable], t.Awaitable[t.Optional[Response]]
]
T = t.TypeVar("T")


class FunctionBasedMiddleware:
    """
    Convert ASGI Middleware to a Node-like Middleware.

    Usage: Example 1
    @middleware()
    def my_middleware(context: IExecution, call_next):
        print("Called my_middleware")
        request = context.switch_to_http_connection().get_request()
        request.state.my_middleware = True
        await call_next()

    Usage: Example 2
    @middleware()
    def my_middleware(context: IExecution, call_next):
        print("Called my_middleware")
        response = context.switch_to_http_connection().get_response()
        response.content = "Some Content"
        response.status_code = 200
        return response
    """

    def __init__(
        self, app: ASGIApp, dispatch: t.Optional[DispatchFunction] = None
    ) -> None:
        self.app = app
        self.dispatch_function = dispatch or self.dispatch

    async def dispatch(
        self, context: IHostContext, call_next: AwaitableCallable
    ) -> Response:
        raise NotImplementedError()  # pragma: no cover

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope, receive)

        if not connection.service_provider:  # pragma: no cover
            raise Exception("Service Provider is required")

        context_factory = connection.service_provider.get(IHostContextFactory)
        context = context_factory.create_context(scope, receive, send)

        async def call_next() -> None:
            await self.app(scope, receive, send)

        response = await self.dispatch_function(context, call_next)

        if response and isinstance(response, Response):
            await response(scope, receive, send)
