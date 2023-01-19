from ellar.di import EllarInjector
from ellar.di.exceptions import ServiceUnavailable
from ellar.services.reflector import Reflector

from .context import (
    ExecutionContextFactory,
    HostContextFactory,
    IExecutionContext,
    IExecutionContextFactory,
    IHostContext,
    IHostContextFactory,
    IHTTPConnectionContextFactory,
    IWebSocketContextFactory,
)
from .context.factory import HTTPConnectionContextFactory, WebSocketContextFactory
from .exceptions.interfaces import IExceptionMiddlewareService
from .exceptions.service import ExceptionMiddlewareService


class CoreServiceRegistration:
    """Create Binding for all application service"""

    __slots__ = ("injector",)

    def __init__(self, injector: EllarInjector) -> None:
        self.injector = injector

    def register_execution_host_context(self) -> None:
        def resolve_execution_host_context() -> IHostContext:
            raise ServiceUnavailable("Service Unavailable at the current context.")

        self.injector.container.register_scoped(
            IExecutionContext, resolve_execution_host_context
        )

    def register_all(self) -> None:
        self.injector.container.register(
            IExceptionMiddlewareService, ExceptionMiddlewareService
        )

        self.injector.container.register(
            IExecutionContextFactory, ExecutionContextFactory
        )
        self.injector.container.register(IHostContextFactory, HostContextFactory)

        self.injector.container.register_scoped(
            IHTTPConnectionContextFactory, HTTPConnectionContextFactory
        )

        self.injector.container.register_scoped(
            IWebSocketContextFactory, WebSocketContextFactory
        )

        self.injector.container.register_instance(Reflector())
        self.register_execution_host_context()
