import typing as t

from ellar.auth import AppIdentitySchemes, IdentityAuthenticationService
from ellar.auth.session import SessionServiceNullStrategy, SessionStrategy
from ellar.common import (
    GlobalGuard,
    GuardCanActivate,
    IApplicationReady,
    IApplicationShutdown,
    IApplicationStartup,
    IExceptionMiddlewareService,
    IExecutionContext,
    IExecutionContextFactory,
    IGuardsConsumer,
    IHostContext,
    IHostContextFactory,
    IHTTPConnectionContextFactory,
    IIdentitySchemes,
    IInterceptorsConsumer,
    IWebSocketContextFactory,
    Module,
)
from ellar.core import ModuleSetup
from ellar.core.conf import Config
from ellar.core.exceptions.service import ExceptionMiddlewareService
from ellar.core.execution_context import ExecutionContextFactory, HostContextFactory
from ellar.core.execution_context.factory import (
    HTTPConnectionContextFactory,
    WebSocketContextFactory,
)
from ellar.core.guards import GuardConsumer
from ellar.core.interceptors import EllarInterceptorConsumer
from ellar.core.services import Reflector, reflector
from ellar.di import EllarInjector, ProviderConfig, injectable, request_scope
from ellar.di.injector.tree_manager import ModuleTreeManager

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.app import App


def _raise_unavailable_exception() -> None:
    raise Exception("Service is only available during request")


@injectable
class GlobalCanActivatePlaceHolder(GuardCanActivate):
    placeholder: bool = True

    async def can_activate(self, context: IExecutionContext) -> bool:
        return True


def get_core_module(app_module: t.Union[t.Type, t.Any], config: Config) -> t.Type:
    @Module(
        modules=[app_module],
        providers=[
            ProviderConfig(
                Config,
                use_value=config,
                export=True,
            ),
            ProviderConfig(
                GlobalGuard,
                use_class=GlobalCanActivatePlaceHolder,
                export=True,
            ),
            ProviderConfig(
                ModuleTreeManager,
                use_value=lambda: config.MODULE_TREE_MANAGER_CLASS(
                    ModuleSetup(EllarCoreModule)
                ),
                export=True,
            ),
            ProviderConfig(
                IExceptionMiddlewareService,
                use_class=ExceptionMiddlewareService,
                export=True,
            ),
            ProviderConfig(
                IExecutionContextFactory, use_class=ExecutionContextFactory, export=True
            ),
            ProviderConfig(
                IHostContextFactory, use_class=HostContextFactory, export=True
            ),
            ProviderConfig(
                IHostContext,
                use_value=_raise_unavailable_exception,
                scope=request_scope,
                export=True,
            ),
            ProviderConfig(
                IExecutionContext,
                use_value=_raise_unavailable_exception,
                scope=request_scope,
                export=True,
            ),
            ProviderConfig(
                IHTTPConnectionContextFactory,
                use_class=HTTPConnectionContextFactory,
                export=True,
            ),
            ProviderConfig(
                IWebSocketContextFactory, use_class=WebSocketContextFactory, export=True
            ),
            ProviderConfig(Reflector, use_value=reflector, export=True),
            ProviderConfig(
                IInterceptorsConsumer, use_value=EllarInterceptorConsumer, export=True
            ),
            ProviderConfig(IGuardsConsumer, use_class=GuardConsumer, export=True),
            ProviderConfig(IIdentitySchemes, use_class=AppIdentitySchemes, export=True),
            ProviderConfig(
                IdentityAuthenticationService,
                use_class=IdentityAuthenticationService,
                export=True,
            ),
            ProviderConfig(
                SessionStrategy, use_class=SessionServiceNullStrategy, export=True
            ),
        ],
    )
    class EllarCoreModule(IApplicationReady, IApplicationStartup, IApplicationShutdown):
        def __init__(self, _config: Config, injector: EllarInjector) -> None:
            self.config = _config
            self.injector = injector

        def on_ready(self, app: "App") -> None:
            pass

        async def on_startup(self, app: "App") -> None:
            pass

        async def on_shutdown(self) -> None:
            pass

    return EllarCoreModule
