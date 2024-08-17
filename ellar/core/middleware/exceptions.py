import typing as t

from ellar.common import APIException, IExceptionMiddlewareService
from ellar.common.interfaces import IHostContextFactory
from ellar.common.types import ASGIApp, TMessage, TReceive, TScope, TSend
from ellar.core.conf import Config
from ellar.core.exceptions.service import ExceptionMiddlewareService
from ellar.core.execution_context import current_injector
from starlette.exceptions import HTTPException

from .middleware import EllarMiddleware


class ExceptionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        exception_middleware_service: IExceptionMiddlewareService,
        config: Config,
    ) -> None:
        self.app = app
        self.debug = config.DEBUG
        self._exception_middleware_service: ExceptionMiddlewareService = t.cast(
            ExceptionMiddlewareService, exception_middleware_service
        )

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        response_started = False

        async def sender(message: TMessage) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, sender)
        except Exception as exc:
            handler = None

            if isinstance(exc, (HTTPException, APIException)):
                handler = self._exception_middleware_service.lookup_status_code_exception_handler(
                    exc.status_code
                )

            if handler is None:
                handler = self._exception_middleware_service.lookup_exception_handler(
                    exc
                )

            if handler is None:
                raise exc

            if response_started:
                msg = "Caught handled exception, but response already started."
                raise RuntimeError(msg) from exc

            context_factory = current_injector.get(IHostContextFactory)
            context = context_factory.create_context(scope)

            if context.get_type() == "http":
                response = await handler.catch(context, exc)
                if not response and not response_started:
                    msg = "HTTP ExceptionHandler must return a response."
                    raise RuntimeError(msg) from exc
                await response(scope, receive, sender)
            elif context.get_type() == "websocket":
                ws_context = context_factory.create_context(scope, receive, send)
                await handler.catch(ws_context, exc)


# ExceptionMiddleware Configuration
exception_middleware = EllarMiddleware(ExceptionMiddleware)
