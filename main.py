import typing as t
from starlette.datastructures import State, URLPath
from starletteapi.middleware.di import RequestServiceProviderMiddleware
from starletteapi.middleware.exceptions import ExceptionMiddleware
from starlette.middleware import Middleware
from starlette.routing import BaseRoute
from starletteapi.logger import logger
from starletteapi.middleware.versioning import RequestVersioningMiddleware
from starletteapi.events import RouterEventManager, ApplicationEventManager
from starletteapi.types import TScope, TReceive, TSend, ASGIApp, T
from starletteapi.middleware.errors import ServerErrorMiddleware
from starletteapi.di.injector import StarletteInjector
from starletteapi.guard import GuardCanActivate
from starletteapi.module import ApplicationModule, BaseModule, StarletteAPIModuleBase
from starletteapi.routing import AppRoutes, AppRouter
from starletteapi.conf import Config
from starletteapi.templating import StarletteAppTemplating, Environment


class StarletteApp(StarletteAppTemplating):
    def __init__(self, module: t.Optional[t.Union[ApplicationModule, t.Type]] = None):
        if module:
            assert isinstance(module, ApplicationModule), "Only ApplicationModule is allowed"
        self._app_module = module or ApplicationModule()(type("StarletteApp", (), {}))

        self.on_startup = RouterEventManager(module.get_startup_events())
        self.on_shutdown = RouterEventManager(module.get_shutdown_events())

        self._config = Config(app_configured=True)
        self.state = State()

        before = ApplicationEventManager(module.get_before_events())
        before.run(config=self.config)

        after = ApplicationEventManager(module.get_after_events())

        self.router = AppRouter(
            routes=AppRoutes(self._app_module),
            redirect_slashes=self.config.REDIRECT_SLASHES,
            on_startup=[self.on_startup.async_run], on_shutdown=[self.on_shutdown.async_run],
            default=self.config.DEFAULT_NOT_FOUND_HANDLER, lifespan=self.config.DEFAULT_LIFESPAN_HANDLER
        )
        # TODO: read auto_bind from configure
        self._injector = StarletteInjector(app=self, auto_bind=False)
        self.middleware_stack = self.build_middleware_stack()

        self._static_app: t.Optional[ASGIApp] = None

        if self.has_static_files:
            self._static_app = self.create_static_app()

            async def _statics(scope: TScope, receive: TReceive, send: TSend):
                return await self._static_app(scope, receive, send)

            self.router.mount(
                self.config.STATIC_MOUNT_PATH, app=_statics, name='static'
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
        logger.info(f'APP SETTINGS: {self._config.config_module}')

    def install_module(
            self, module: t.Union[t.Type[StarletteAPIModuleBase], BaseModule, t.Type[T]], **init_kwargs: t.Any
    ) -> t.Union[StarletteAPIModuleBase, BaseModule, T]:
        _module_instance, installed = self._app_module.add_module(
            container=self._injector.container, module=module, **init_kwargs
        )
        if installed:
            self.reload_static_app()
            self.router.routes.reload_routes()
            self.on_startup.reload(self._app_module.get_startup_events())
            self.on_shutdown.reload(self._app_module.get_startup_events())

            if isinstance(_module_instance, BaseModule):
                after = ApplicationEventManager(list(_module_instance.after_initialisation))
                after.run(application=self)
        return _module_instance

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._app_module.global_guards

    def use_global_guards(self, *guards: 'GuardCanActivate') -> None:
        self._app_module.global_guards.extend(guards)

    @property
    def injector(self) -> StarletteInjector:
        return self._injector

    @property
    def has_static_files(self) -> bool:
        return True if self.static_files or self.config.STATIC_FOLDER_PACKAGES else False

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, value):
        ...

    def build_middleware_stack(self) -> ASGIApp:
        error_handler = None
        exception_handlers = {}

        for key, value in self.config.EXCEPTION_HANDLERS.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=self.debug)]
            + self.config.MIDDLEWARE
            + [
                Middleware(
                    ExceptionMiddleware, handlers=exception_handlers, debug=self.debug
                ),
                Middleware(RequestVersioningMiddleware, debug=self.debug, config=self.config),
                Middleware(RequestServiceProviderMiddleware, debug=self.debug, injector=self.injector),
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
    def debug(self) -> bool:
        return self.config.DEBUG

    @debug.setter
    def debug(self, value: bool) -> None:
        self.config.DEBUG = value
        self.build_middleware_stack()

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
