import typing as t

from ellar.auth import AppIdentitySchemes
from ellar.auth.session import ISessionStrategy, SessionServiceNullStrategy
from ellar.common import (
    IExceptionMiddlewareService,
    IExecutionContextFactory,
    IGuardsConsumer,
    IHostContextFactory,
    IHTTPConnectionContextFactory,
    IIdentitySchemes,
    IInterceptorsConsumer,
    IWebSocketContextFactory,
)
from ellar.core.exceptions.service import ExceptionMiddlewareService
from ellar.core.execution_context import ExecutionContextFactory, HostContextFactory
from ellar.core.execution_context.factory import (
    HTTPConnectionContextFactory,
    WebSocketContextFactory,
)
from ellar.core.guards import GuardConsumer
from ellar.core.interceptors import EllarInterceptorConsumer
from ellar.core.services import Reflector, reflector
from ellar.di import EllarInjector

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.conf import Config


class EllarAppService:
    """Create Binding for all application service"""

    __slots__ = ("injector", "config")

    def __init__(self, injector: EllarInjector, config: "Config") -> None:
        self.injector = injector
        self.config = config

    def register_core_services(self) -> None:
        self.injector.container.register(
            IExceptionMiddlewareService, ExceptionMiddlewareService
        )

        self.injector.container.register(
            IExecutionContextFactory, ExecutionContextFactory
        )
        self.injector.container.register(IHostContextFactory, HostContextFactory)

        self.injector.container.register(
            IHTTPConnectionContextFactory, HTTPConnectionContextFactory
        )

        self.injector.container.register(
            IWebSocketContextFactory, WebSocketContextFactory
        )

        self.injector.container.register_instance(reflector, Reflector)
        self.injector.container.register(
            IInterceptorsConsumer, EllarInterceptorConsumer
        )
        self.injector.container.register_singleton(IGuardsConsumer, GuardConsumer)
        self.injector.container.register_singleton(IIdentitySchemes, AppIdentitySchemes)
        self.injector.container.register_singleton(
            ISessionStrategy, SessionServiceNullStrategy
        )
