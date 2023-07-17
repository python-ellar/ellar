import typing as t

from ellar.auth import AppIdentitySchemes, IIdentitySchemes
from ellar.auth.session import ISessionStrategy, SessionServiceNullStrategy
from ellar.common import (
    IExceptionMiddlewareService,
    IExecutionContextFactory,
    IGuardsConsumer,
    IHostContextFactory,
    IHTTPConnectionContextFactory,
    IInterceptorsConsumer,
    IWebSocketContextFactory,
)
from ellar.core.services import Reflector
from ellar.di import EllarInjector

from .context import ExecutionContextFactory, HostContextFactory
from .context.factory import HTTPConnectionContextFactory, WebSocketContextFactory
from .exceptions.service import ExceptionMiddlewareService
from .guards import GuardConsumer
from .interceptors import EllarInterceptorConsumer

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.conf import Config


class EllarCoreService:
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

        self.injector.container.register_scoped(
            IHTTPConnectionContextFactory, HTTPConnectionContextFactory
        )

        self.injector.container.register_scoped(
            IWebSocketContextFactory, WebSocketContextFactory
        )

        self.injector.container.register(Reflector)
        self.injector.container.register_singleton(
            IInterceptorsConsumer, EllarInterceptorConsumer
        )
        self.injector.container.register_singleton(IGuardsConsumer, GuardConsumer)
        self.injector.container.register_singleton(IIdentitySchemes, AppIdentitySchemes)
        self.injector.container.register_singleton(
            ISessionStrategy, SessionServiceNullStrategy
        )
