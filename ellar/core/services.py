from ellar.di import EllarInjector
from ellar.services.reflector import Reflector

from .context import (
    ExecutionContextFactory,
    HostContextFactory,
    IExecutionContextFactory,
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
