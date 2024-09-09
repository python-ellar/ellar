import typing as t
from contextlib import asynccontextmanager

from ellar.common import IExceptionMiddlewareService
from ellar.common.constants import EXCEPTION_HANDLERS_KEY, MIDDLEWARE_HANDLERS_KEY
from ellar.common.logging import logger
from ellar.common.types import ASGIApp, TReceive, TScope, TSend
from ellar.core.execution_context import injector_context
from ellar.core.middleware import ExceptionMiddleware, ServerErrorMiddleware
from ellar.core.middleware.middleware import EllarMiddleware
from ellar.di import Container
from ellar.reflect import reflect
from starlette.routing import BaseRoute


class ModuleExecutionContext:
    def __init__(self, container: Container, module: t.Type) -> None:
        self.module = module

        self._middleware: t.List = list(
            reflect.get_metadata(MIDDLEWARE_HANDLERS_KEY, self.module) or []
        )

        exception_middleware_class = type(
            container.injector.get(IExceptionMiddlewareService)
        )
        exception_middleware_service = (
            exception_middleware_class().build_exception_handlers(
                *reflect.get_metadata(EXCEPTION_HANDLERS_KEY, self.module) or []
            )
        )

        error_handler = exception_middleware_service.get_500_error_handler()
        self._middleware.insert(
            0,
            EllarMiddleware(
                ExceptionMiddleware,
                exception_middleware_service=exception_middleware_service,
            ),
        )
        if error_handler:
            self._middleware.insert(
                0,
                EllarMiddleware(
                    ServerErrorMiddleware,
                    exception_service=exception_middleware_service,
                ),
            )

        self.container = container

        self._operation: t.Optional[BaseRoute] = None
        self._middleware_stack: t.Optional[ASGIApp] = None

    def _build_middleware_stack(self) -> ASGIApp:
        app = self._app
        for cls, args, kwargs in reversed(self._middleware):
            try:
                app = cls(app, *args, **kwargs)
            except Exception as ex:
                logger.exception(f"Unable to setup middleware='{cls}'")
                raise ex
        return app

    async def _app(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        assert self._operation
        await self._operation.handle(scope, receive, send)

    async def handle(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        if self._middleware_stack is None:
            self._middleware_stack = self._build_middleware_stack()
        await self._middleware_stack(scope, receive, send)

    @asynccontextmanager
    async def context(
        self, operation: BaseRoute
    ) -> t.AsyncGenerator["ModuleExecutionContext", t.Any]:
        async with injector_context(self.container.injector):
            # set Operation
            self._operation = operation

            yield self
            # clear Operation
            self._operation = None
