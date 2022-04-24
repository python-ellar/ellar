import typing as t

from starlette.routing import BaseRoute

from architek.core.conf import Config
from architek.core.context import ExecutionContext, IExecutionContext
from architek.core.datastructures import State, URLPath
from architek.core.events import ApplicationEventManager, RouterEventManager
from architek.core.guard import GuardCanActivate
from architek.core.logger import logger
from architek.core.middleware import (
    ExceptionMiddleware,
    Middleware,
    RequestServiceProviderMiddleware,
    RequestVersioningMiddleware,
    ServerErrorMiddleware,
)
from architek.core.modules import (
    ApplicationModuleDecorator,
    BaseModuleDecorator,
    ModuleBase,
)
from architek.core.routing import ApplicationRouter, RouteCollection
from architek.core.templating import ArchitekAppTemplating, Environment
from architek.di import StarletteInjector
from architek.types import ASGIApp, T, TReceive, TScope, TSend


class ArchitekApp(ArchitekAppTemplating):
    def __init__(self, module: t.Optional[ApplicationModuleDecorator] = None):
        if module:
            assert isinstance(
                module, ApplicationModuleDecorator
            ), "Only ApplicationModule is allowed"
        self._app_module = module or ApplicationModuleDecorator()(
            type("StarletteApp", (), {})
        )

        self.on_startup = RouterEventManager(self._app_module.get_startup_events())
        self.on_shutdown = RouterEventManager(self._app_module.get_shutdown_events())

        self._config = Config(app_configured=True)
        self.state = State()

        before = ApplicationEventManager(self._app_module.get_before_events())
        before.run(config=self.config)

        after = ApplicationEventManager(self._app_module.get_after_events())

        self.router = ApplicationRouter(
            routes=RouteCollection(self._app_module),
            redirect_slashes=t.cast(bool, self.config.REDIRECT_SLASHES),
            on_startup=[self.on_startup.async_run],
            on_shutdown=[self.on_shutdown.async_run],
            default=self.config.DEFAULT_NOT_FOUND_HANDLER,  # type: ignore
            lifespan=self.config.DEFAULT_LIFESPAN_HANDLER,  # type: ignore
        )
        # TODO: read auto_bind from configure
        self._injector = StarletteInjector(app=self, auto_bind=False)
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

        self._injector.container.install(module=self._app_module)
        self._finalize_app_initialization()
        after.run(application=self)
        logger.info(f"APP SETTINGS: {self._config.config_module}")

    def install_module(
        self,
        module: t.Union[t.Type[T], t.Type[ModuleBase], BaseModuleDecorator],
        **init_kwargs: t.Any,
    ) -> t.Union[T, ModuleBase, BaseModuleDecorator]:
        _module_instance, installed = self._app_module.add_module(
            container=self._injector.container, module=module, **init_kwargs
        )
        if installed:
            self.reload_static_app()
            self.router.routes.reload_routes()
            self.on_startup.reload(self._app_module.get_startup_events())
            self.on_shutdown.reload(self._app_module.get_startup_events())

            if isinstance(_module_instance, BaseModuleDecorator):
                after = ApplicationEventManager(
                    list(_module_instance.after_initialisation)
                )
                after.run(application=self)
        return _module_instance

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._app_module.global_guards

    def use_global_guards(self, *guards: "GuardCanActivate") -> None:
        self._app_module.global_guards.extend(guards)

    @property
    def injector(self) -> StarletteInjector:
        return self._injector

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

        configured_exception_handlers = t.cast(dict, self.config.EXCEPTION_HANDLERS)
        for key, value in configured_exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        configured_middleware = t.cast(list, self.config.MIDDLEWARE)
        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=self.debug)]
            + configured_middleware
            + [
                Middleware(
                    ExceptionMiddleware, handlers=exception_handlers, debug=self.debug
                ),
                Middleware(
                    RequestVersioningMiddleware, debug=self.debug, config=self.config
                ),
                Middleware(
                    RequestServiceProviderMiddleware,
                    debug=self.debug,
                    injector=self.injector,
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

    @property
    def debug(self) -> bool:  # type: ignore
        return t.cast(bool, self.config.DEBUG)

    def url_path_for(self, name: str, **path_params: t.Any) -> URLPath:
        return self.router.url_path_for(name, **path_params)

    def mount(self, path: str, app: ASGIApp, name: str = None) -> None:
        self.router.mount(path, app=app, name=name)

    def host(self, host: str, app: ASGIApp, name: str = None) -> None:
        self.router.host(host, app=app, name=name)

    def _finalize_app_initialization(self) -> None:
        self.injector.container.add_instance(self)
        self.injector.container.add_instance(self.config, Config)
        self.injector.container.add_instance(self.jinja_environment, Environment)
        self.injector.container.add_scoped(IExecutionContext, ExecutionContext)
