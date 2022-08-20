import typing as t

from starlette.routing import BaseRoute, Mount

from ellar.core.conf import Config
from ellar.core.context import ExecutionContext, IExecutionContext
from ellar.core.datastructures import State, URLPath
from ellar.core.events import EventHandler, RouterEventManager
from ellar.core.guard import GuardCanActivate
from ellar.core.middleware import (
    ExceptionMiddleware,
    Middleware,
    RequestServiceProviderMiddleware,
    RequestVersioningMiddleware,
)
from ellar.core.modules import ModuleBase, ModuleTemplateRef
from ellar.core.modules.ref import create_module_ref_factor
from ellar.core.routing import ApplicationRouter
from ellar.core.templating import AppTemplating, Environment
from ellar.core.versioning import VERSIONING, BaseAPIVersioning
from ellar.di.injector import EllarInjector
from ellar.di.providers import ModuleProvider
from ellar.logger import logger
from ellar.services.reflector import Reflector
from ellar.types import ASGIApp, T, TReceive, TScope, TSend


class App(AppTemplating):
    def __init__(
        self,
        config: Config,
        injector: EllarInjector,
        on_startup_event_handlers: t.Optional[t.Sequence[EventHandler]] = None,
        on_shutdown_event_handlers: t.Optional[t.Sequence[EventHandler]] = None,
        lifespan: t.Optional[t.Callable[["App"], t.AsyncContextManager]] = None,
        global_guards: t.List[
            t.Union[t.Type[GuardCanActivate], GuardCanActivate]
        ] = None,
    ):
        assert isinstance(config, Config), "config must instance of Config"
        assert isinstance(
            injector, EllarInjector
        ), "injector must instance of EllarInjector"

        # The lifespan context function is a newer style that replaces
        # on_startup / on_shutdown handlers. Use one or the other, not both.
        assert lifespan is None or (
            on_startup_event_handlers is None and on_shutdown_event_handlers is None
        ), "Use either 'lifespan' or 'on_startup'/'on_shutdown', not both."

        self._config = config
        # TODO: read auto_bind from configure
        self._injector: EllarInjector = injector

        self._global_guards = [] if global_guards is None else list(global_guards)
        self._exception_handlers = dict(t.cast(dict, self.config.EXCEPTION_HANDLERS))
        self._user_middleware = list(t.cast(list, self.config.MIDDLEWARE))

        self.on_startup = RouterEventManager(
            [] if on_startup_event_handlers is None else list(on_startup_event_handlers)
        )
        self.on_shutdown = RouterEventManager(
            []
            if on_shutdown_event_handlers is None
            else list(on_shutdown_event_handlers)
        )

        self._static_app: t.Optional[ASGIApp] = None

        self.state = State()
        self.config.DEFAULT_LIFESPAN_HANDLER = (
            lifespan or self.config.DEFAULT_LIFESPAN_HANDLER
        )
        self.router = ApplicationRouter(
            routes=self._get_module_routes(),
            redirect_slashes=t.cast(bool, self.config.REDIRECT_SLASHES),
            on_startup=[self.on_startup.async_run],
            on_shutdown=[self.on_shutdown.async_run],
            default=self.config.DEFAULT_NOT_FOUND_HANDLER,  # type: ignore
            lifespan=self.config.DEFAULT_LIFESPAN_HANDLER,  # type: ignore
        )
        self.middleware_stack = self.build_middleware_stack()
        self._finalize_app_initialization()

        logger.info(f"APP SETTINGS: {self._config.config_module}")

    def _statics_wrapper(self) -> t.Callable:
        async def _statics_func_wrapper(
            scope: TScope, receive: TReceive, send: TSend
        ) -> t.Any:
            assert self._static_app, 'app static ASGIApp can not be "None"'
            return await self._static_app(scope, receive, send)

        return _statics_func_wrapper

    def _get_module_routes(self) -> t.List[BaseRoute]:
        _routes: t.List[BaseRoute] = []
        if self.has_static_files:
            self._static_app = self.create_static_app()
            _routes.append(
                Mount(
                    str(self.config.STATIC_MOUNT_PATH),
                    app=self._statics_wrapper(),
                    name="static",
                )
            )

        for _, module_ref in self._injector.get_modules().items():
            module_ref.run_module_register_services()
            _routes.extend(module_ref.routes)

        return _routes

    def install_module(
        self,
        module: t.Union[t.Type[T], t.Type[ModuleBase]],
        **init_kwargs: t.Any,
    ) -> t.Union[T, ModuleBase]:
        module_ref = self.injector.get_module(module)
        if module_ref:
            return module_ref.get_module_instance()

        module_ref = create_module_ref_factor(
            module, container=self.injector.container, config=self.config, **init_kwargs
        )
        self.injector.add_module(module_ref)
        self.middleware_stack = self.build_middleware_stack()

        if isinstance(module_ref, ModuleTemplateRef):
            module_ref.run_module_register_services()
            self.router.extend(module_ref.routes)
            self.reload_static_app()
            module_ref.run_application_ready(self)

        return t.cast(T, module_ref.get_module_instance())

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    def use_global_guards(
        self, *guards: t.Union["GuardCanActivate", t.Type["GuardCanActivate"]]
    ) -> None:
        self._global_guards.extend(guards)

    @property
    def injector(self) -> EllarInjector:
        return self._injector

    @property
    def versioning_scheme(self) -> BaseAPIVersioning:
        return t.cast(BaseAPIVersioning, self._config.VERSIONING_SCHEME)

    @property
    def has_static_files(self) -> bool:  # type: ignore
        return (
            True if self.static_files or self.config.STATIC_FOLDER_PACKAGES else False
        )

    @property
    def config(self) -> Config:  # type: ignore
        return self._config

    def build_middleware_stack(self) -> ASGIApp:
        error_handler = None
        exception_handlers = {}

        for key, value in self._exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middleware = (
            [
                Middleware(
                    RequestServiceProviderMiddleware,
                    debug=self.debug,
                    injector=self.injector,
                    handler=error_handler,
                ),
                Middleware(
                    RequestVersioningMiddleware, debug=self.debug, config=self.config
                ),
            ]
            + self._user_middleware
            + [
                Middleware(
                    ExceptionMiddleware, handlers=exception_handlers, debug=self.debug
                ),
            ]
        )

        app = self.router
        for cls, options in reversed(middleware):
            app = cls(app=app, **options)
        return app

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        scope["app"] = self
        await self.middleware_stack(scope, receive, send)

    @property
    def routes(self) -> t.List[BaseRoute]:
        return self.router.routes.get_routes()

    def url_path_for(self, name: str, **path_params: t.Any) -> URLPath:
        return self.router.url_path_for(name, **path_params)

    def enable_versioning(
        self,
        schema: VERSIONING,
        version_parameter: str = "version",
        default_version: t.Optional[str] = None,
        **init_kwargs: t.Any,
    ) -> None:
        self.config.VERSIONING_SCHEME = schema.value(
            version_parameter=version_parameter,
            default_version=default_version,
            **init_kwargs,
        )

    def _run_module_application_ready(
        self,
    ) -> None:
        for _, module_ref in self.injector.get_templating_modules().items():
            module_ref.run_application_ready(self)

    def _finalize_app_initialization(self) -> None:
        self.injector.container.register_instance(self)
        self.injector.container.register_instance(Reflector())
        self.injector.container.register_instance(self.config, Config)
        self.injector.container.register_instance(self.jinja_environment, Environment)
        self.injector.container.register_scoped(
            IExecutionContext,
            ModuleProvider(ExecutionContext, scope={}, receive=None, send=None),
        )
        self._run_module_application_ready()

    def add_exception_handler(
        self,
        exc_class_or_status_code: t.Union[int, t.Type[Exception]],
        handler: t.Callable,
    ) -> None:  # pragma: no cover
        self._exception_handlers[exc_class_or_status_code] = handler
        self.middleware_stack = self.build_middleware_stack()

    def exception_handler(
        self, exc_class_or_status_code: t.Union[int, t.Type[Exception]]
    ) -> t.Callable:  # pragma: nocover
        def decorator(func: t.Callable) -> t.Callable:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return decorator
