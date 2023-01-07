import typing as t

from starlette.middleware.errors import ServerErrorMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse

from ellar.constants import SCOPE_RESPONSE_STARTED, SCOPE_SERVICE_PROVIDER
from ellar.core.connection.http import Request
from ellar.core.context import IHostContext
from ellar.core.response import Response
from ellar.di import EllarInjector
from ellar.types import ASGIApp, TMessage, TReceive, TScope, TSend

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.exceptions.interfaces import IExceptionHandler


class RequestServiceProviderMiddleware(ServerErrorMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        debug: bool,
        injector: "EllarInjector",
        handler: "IExceptionHandler" = None
    ) -> None:
        _handler = None
        if handler:
            self._500_error_handler = handler
            _handler = self.error_handler

        super(RequestServiceProviderMiddleware, self).__init__(
            debug=debug, handler=_handler, app=app
        )

        self.injector = injector

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ["http", "websocket"]:  # pragma: no cover
            await super().__call__(scope, receive, send)
            return

        scope[SCOPE_RESPONSE_STARTED] = False

        async def sender(message: TMessage) -> None:
            if message["type"] == "http.response.start":
                scope[SCOPE_RESPONSE_STARTED] = True
            await send(message)
            return

        async with self.injector.create_asgi_args(
            scope, receive, sender
        ) as service_provider:
            scope[SCOPE_SERVICE_PROVIDER] = service_provider

            host_context: IHostContext = service_provider.get(IHostContext)

            if host_context.get_type() == "http":
                await super().__call__(*host_context.get_args())
            else:
                await self.app(*host_context.get_args())

    async def error_handler(self, request: Request, exc: Exception) -> Response:
        host_context = request.scope[SCOPE_SERVICE_PROVIDER].get(IHostContext)
        assert self._500_error_handler
        response = await self._500_error_handler.catch(host_context, exc)
        return response

    def error_response(self, request: StarletteRequest, exc: Exception) -> Response:
        return JSONResponse(
            dict(detail="Internal server error", status_code=500), status_code=500
        )
