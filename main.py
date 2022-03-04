import typing as t
from starlette.applications import Starlette
from starlette.datastructures import State, URLPath
from starletteapi.middleware.di import RequestServiceProviderMiddleware
from starletteapi.middleware.exceptions import ExceptionMiddleware
from starlette.middleware import Middleware
from starlette.routing import BaseRoute

from starletteapi.middleware.versioning import RequestVersioningMiddleware
from starletteapi.types import TScope, TReceive, TSend, ASGIApp
from starletteapi.middleware.errors import ServerErrorMiddleware
from starletteapi.di.injector import StarletteInjector
from starletteapi.guard import GuardCanActivate
from starletteapi.module import ApplicationModule, BaseModule, StarletteAPIModuleBase
from starletteapi.routing import APIRouter
from starletteapi.conf import Config
from starletteapi.templating import StarletteAppTemplating, Environment

T = t.TypeVar('T')


class StarletteApp(StarletteAppTemplating):
    def __init__(
            self,
            *,
            app_module: ApplicationModule,
            routes: t.Sequence[BaseRoute] = None,
            global_guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None,
            on_startup: t.Sequence[t.Callable] = None,
            on_shutdown: t.Sequence[t.Callable] = None,
            lifespan: t.Callable[["Starlette"], t.AsyncContextManager] = None,
    ):
        self._global_guards = global_guards or []

        self._config = Config(app_configured=True)
        self._debug = self.config.validate_config.DEBUG
        self.state = State()

        self._app_module = app_module

        self.router = APIRouter(
            routes, on_startup=on_startup, on_shutdown=on_shutdown,
            lifespan=lifespan, redirect_slashes=self.config.validate_config.REDIRECT_SLASHES
        )

        self._injector = StarletteInjector(app=self, auto_bind=False)
        self.middleware_stack = self.build_middleware_stack()

        self._static_app: t.Optional[ASGIApp] = None

        if self.static_files or self.config.validate_config.STATIC_FOLDER_PACKAGES:
            self._static_app = self.create_static_app()

            async def _statics(scope: TScope, receive: TReceive, send: TSend):
                return await self._static_app(scope, receive, send)

            self.router.mount(
                self.config.validate_config.STATIC_MOUNT_PATH, app=_statics, name='static'
            )

        self.Get = self.router.Get
        self.Post = self.router.Post

        self.Delete = self.router.Delete
        self.Patch = self.router.Patch

        self.Put = self.router.Put
        self.Options = self.router.Options

        self.Trace = self.router.Trace
        self.Head = self.router.Head

        self.Route = self.router.Route
        self.Websocket = self.router.Websocket
        self._injector.container.install(module=self._app_module)
        self._finalize_app_initialization()

    def install_module(
            self, module: t.Union[t.Type[StarletteAPIModuleBase], BaseModule, t.Type[T]]
    ) -> t.Union[StarletteAPIModuleBase, BaseModule, T]:
        _module_instance, installed = self._app_module.add_module(
            container=self._injector.container, module=module
        )
        if installed:
            self.reload_static_app()
        return _module_instance

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    @property
    def injector(self) -> StarletteInjector:
        return self._injector

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, value):
        ...

    def build_middleware_stack(self) -> ASGIApp:
        error_handler = None
        exception_handlers = {}

        for key, value in self.config.validate_config.EXCEPTION_HANDLERS.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=self._debug)]
            + self.config.validate_config.MIDDLEWARE
            + [
                Middleware(
                    ExceptionMiddleware, handlers=exception_handlers, debug=self._debug
                ),
                Middleware(RequestVersioningMiddleware, debug=self._debug, config=self.config),
                Middleware(RequestServiceProviderMiddleware, debug=self._debug, injector=self.injector),
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
        return self.router.routes

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self._debug = value
        self.config.validate_config.DEBUG = value
        self.middleware_stack = self.build_middleware_stack()

    def url_path_for(self, name: str, **path_params: t.Any) -> URLPath:
        return self.router.url_path_for(name, **path_params)

    # The following usages are now discouraged in favour of configuration
    #  during Starlette.__init__(...)
    def on_event(self, event_type: str) -> t.Callable:
        return self.router.on_event(event_type)

    def mount(self, path: str, app: ASGIApp, name: str = None) -> None:
        self.router.mount(path, app=app, name=name)

    def host(self, host: str, app: ASGIApp, name: str = None) -> None:
        self.router.host(host, app=app, name=name)

    def _finalize_app_initialization(self) -> None:
        self.injector.container.add_instance(self)
        self.injector.container.add_instance(self.config, Config)
        self.injector.container.add_instance(self.jinja_environment, Environment)
        self._app_module.module.on_app_ready(self)
