import typing as t

from starlette.responses import Response
from starlette.routing import BaseRoute

from ellar.core.conf import Config
from ellar.core.connection import Request
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
from ellar.core.modules import BaseModuleDecorator, ModuleBase
from ellar.core.modules.module import ModuleBuilder
from ellar.core.routing import ApplicationRouter
from ellar.core.templating import AppTemplating, Environment
from ellar.core.versioning import VERSIONING, BaseAPIVersioning
from ellar.di.injector import StarletteInjector
from ellar.logger import logger
from ellar.types import ASGIApp, T, TReceive, TScope, TSend


class App(AppTemplating):
    def __init__(
        self,
        config: Config = None,
        routes: t.Optional[t.Sequence[BaseRoute]] = None,
        middleware: t.Optional[t.Sequence[Middleware]] = None,
        exception_handlers: t.Optional[
            t.Mapping[
                t.Any,
                t.Callable[
                    [Request, Exception],
                    t.Union[Response, t.Awaitable[Response]],
                ],
            ]
        ] = None,
        on_startup_event_handlers: t.Optional[t.Sequence[EventHandler]] = None,
        on_shutdown_event_handlers: t.Optional[t.Sequence[EventHandler]] = None,
        lifespan: t.Optional[t.Callable[["App"], t.AsyncContextManager]] = None,
        modules: t.Dict[t.Type[ModuleBase], BaseModuleDecorator] = None,
        global_guards: t.List[
            t.Union[t.Type[GuardCanActivate], GuardCanActivate]
        ] = None,
    ):
        self._config = config or Config(app_configured=True)
        # TODO: read auto_bind from configure
        self._injector = StarletteInjector(auto_bind=False)

        self._global_guards = [] if global_guards is None else list(global_guards)
        _exception_handlers = (
            {} if exception_handlers is None else dict(exception_handlers)
        )
        self._exception_handlers = dict(t.cast(dict, self.config.EXCEPTION_HANDLERS))
        self._exception_handlers.update(_exception_handlers)
        self._modules = {} if modules is None else dict(modules)

        _user_middleware = [] if middleware is None else list(middleware)
        self._user_middleware = list(t.cast(list, self.config.MIDDLEWARE))
        self._user_middleware.extend(_user_middleware)

        self.on_startup = RouterEventManager(
            [] if on_startup_event_handlers is None else list(on_startup_event_handlers)
        )
        self.on_shutdown = RouterEventManager(
            []
            if on_shutdown_event_handlers is None
            else list(on_shutdown_event_handlers)
        )

        self.state = State()

        self.router = ApplicationRouter(
            routes=routes or [],
            redirect_slashes=t.cast(bool, self.config.REDIRECT_SLASHES),
            on_startup=[self.on_startup.async_run],
            on_shutdown=[self.on_shutdown.async_run],
            default=self.config.DEFAULT_NOT_FOUND_HANDLER,  # type: ignore
            lifespan=lifespan or self.config.DEFAULT_LIFESPAN_HANDLER,  # type: ignore
        )
        self.middleware_stack = self.build_middleware_stack()

        self._static_app: t.Optional[ASGIApp] = None

        if self.has_static_files:
            self._static_app = self.create_static_app()

            async def _statics(scope: TScope, receive: TReceive, send: TSend) -> t.Any:
                return await self._static_app(scope, receive, send)  # type: ignore

            self.router.mount(
                self.config.STATIC_MOUNT_PATH,  # type: ignore
                app=_statics,
                name="static",
            )

        self.Get = self.router.Get
        self.Post = self.router.Post

        self.Delete = self.router.Delete
        self.Patch = self.router.Patch

        self.Put = self.router.Put
        self.Options = self.router.Options

        self.Trace = self.router.Trace
        self.Head = self.router.Head

        self.HttpRoute = self.router.HttpRoute
        self.WsRoute = self.router.WsRoute
        self._finalize_app_initialization()

        logger.info(f"APP SETTINGS: {self._config.config_module}")

    def install_module(
        self,
        module: t.Union[t.Type[T], t.Type[ModuleBase], BaseModuleDecorator],
        **init_kwargs: t.Any,
    ) -> t.Union[T, ModuleBase, BaseModuleDecorator]:

        if (
            isinstance(module, BaseModuleDecorator)
            and module.get_module() in self._modules
        ):
            return t.cast(BaseModuleDecorator, self._modules.get(module.get_module()))

        _module_instance = self.injector.container.install(module=module, **init_kwargs)
        modules_data = ModuleBuilder(_module_instance).data

        if isinstance(module, BaseModuleDecorator):
            self._modules.update({module.get_module(): module})

        self.reload_static_app()
        self.router.routes.extend(modules_data.routes)
        self.on_startup.reload(list(self.on_startup) + modules_data.startup_event)
        self.on_shutdown.reload(list(self.on_shutdown) + modules_data.shutdown_event)

        self._exception_handlers.update(modules_data.exception_handlers)
        self._user_middleware.extend(modules_data.middleware)

        self.middleware_stack = self.build_middleware_stack()
        return t.cast(T, _module_instance)

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    def use_global_guards(self, *guards: "GuardCanActivate") -> None:
        self._global_guards.extend(guards)

    @property
    def injector(self) -> StarletteInjector:
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

    def mount(self, path: str, app: ASGIApp, name: str = None) -> None:
        self.router.mount(path, app=app, name=name)

    def host(self, host: str, app: ASGIApp, name: str = None) -> None:
        self.router.host(host, app=app, name=name)

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

    def _finalize_app_initialization(self) -> None:
        self.injector.container.add_instance(self)
        self.injector.container.add_instance(self.config, Config)
        self.injector.container.add_instance(self.jinja_environment, Environment)
        self.injector.container.add_scoped(IExecutionContext, ExecutionContext)
