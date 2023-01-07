import logging
import typing as t

from starlette.routing import BaseRoute, Mount

from ellar.constants import LOG_LEVELS
from ellar.core.conf import Config
from ellar.core.datastructures import State, URLPath
from ellar.core.events import EventHandler, RouterEventManager
from ellar.core.exceptions.interfaces import (
    IExceptionHandler,
    IExceptionMiddlewareService,
)
from ellar.core.guard import GuardCanActivate
from ellar.core.middleware import (
    CORSMiddleware,
    ExceptionMiddleware,
    Middleware,
    RequestServiceProviderMiddleware,
    RequestVersioningMiddleware,
    TrustedHostMiddleware,
)
from ellar.core.modules import ModuleBase, ModuleTemplateRef
from ellar.core.modules.ref import create_module_ref_factor
from ellar.core.routing import ApplicationRouter
from ellar.core.templating import AppTemplating, Environment
from ellar.core.versioning import VERSIONING, BaseAPIVersioning
from ellar.di.injector import EllarInjector
from ellar.logger import logger
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
        self._injector: EllarInjector = injector

        self._global_guards = [] if global_guards is None else list(global_guards)
        self._exception_handlers = list(self.config.EXCEPTION_HANDLERS)

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
            redirect_slashes=self.config.REDIRECT_SLASHES,
            on_startup=[self.on_startup.async_run]
            if self.config.DEFAULT_LIFESPAN_HANDLER is None
            else None,
            on_shutdown=[self.on_shutdown.async_run]
            if self.config.DEFAULT_LIFESPAN_HANDLER is None
            else None,
            default=self.config.DEFAULT_NOT_FOUND_HANDLER,  # type: ignore
            lifespan=self.config.DEFAULT_LIFESPAN_HANDLER,
        )
        self.middleware_stack = self.build_middleware_stack()
        self._finalize_app_initialization()
        self._config_logging()

    def _config_logging(self) -> None:
        log_level = (
            self.config.LOG_LEVEL.value
            if self.config.LOG_LEVEL
            else LOG_LEVELS.info.value
        )
        logging.getLogger("ellar").setLevel(log_level)
        logger.info(f"APP SETTINGS MODULE: {self.config.config_module}")

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
        self.rebuild_middleware_stack()

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
        service_middleware = self.injector.get(IExceptionMiddlewareService)
        service_middleware.build_exception_handlers(*self._exception_handlers)
        error_handler = service_middleware.get_500_error_handler()
        allowed_hosts = self.config.ALLOWED_HOSTS

        if self.debug and allowed_hosts != ["*"]:
            allowed_hosts = ["*"]

        middleware = (
            [
                Middleware(
                    CORSMiddleware,
                    allow_origins=self.config.CORS_ALLOW_ORIGINS,
                    allow_credentials=self.config.CORS_ALLOW_CREDENTIALS,
                    allow_methods=self.config.CORS_ALLOW_METHODS,
                    allow_headers=self.config.CORS_ALLOW_HEADERS,
                    allow_origin_regex=self.config.CORS_ALLOW_ORIGIN_REGEX,
                    expose_headers=self.config.CORS_EXPOSE_HEADERS,
                    max_age=self.config.CORS_MAX_AGE,
                ),
                Middleware(
                    TrustedHostMiddleware,
                    allowed_hosts=allowed_hosts,
                    www_redirect=self.config.REDIRECT_HOST,
                ),
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
                    ExceptionMiddleware,
                    exception_middleware_service=service_middleware,
                    debug=self.debug,
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
        self.injector.container.register_instance(self.config, Config)
        self.injector.container.register_instance(self.jinja_environment, Environment)
        self._run_module_application_ready()

    def add_exception_handler(
        self,
        *exception_handlers: IExceptionHandler,
    ) -> None:
        _added_any = False
        for exception_handler in exception_handlers:
            if exception_handler not in self._exception_handlers:
                self._exception_handlers.append(exception_handler)
                _added_any = True
        if _added_any:
            self.rebuild_middleware_stack()

    def rebuild_middleware_stack(self) -> None:
        self.middleware_stack = self.build_middleware_stack()
