import typing as t
from starlette.applications import Starlette

from starletteapi.middleware.di import DIRequestServiceProviderMiddleware
from starletteapi.middleware.exceptions import ExceptionMiddleware
from starlette.middleware import Middleware
from starlette.routing import BaseRoute

from starletteapi.middleware.versioning import RequestVersioningMiddleware
from starletteapi.static_files import StarletteStaticFiles
from starletteapi.types import TScope, TReceive, TSend, ASGIApp
from starletteapi.middleware.errors import ServerErrorMiddleware
from starletteapi.di.injector import StarletteInjector
from starletteapi.exception_handlers import api_exception_handler, request_validation_exception_handler
from starletteapi.exceptions import RequestValidationError, APIException
from starletteapi.guard import GuardCanActivate
from starletteapi.module import ApplicationModule
from starletteapi.routing import APIRouter
from starletteapi.settings import Config
from starletteapi.templating import StarletteAppTemplating
from starletteapi.versioning import VERSIONING, BaseAPIVersioning


class StarletteApp(Starlette, StarletteAppTemplating):
    def __init__(
            self,
            *,
            root_module: ApplicationModule,
            routes: t.Sequence[BaseRoute] = None,
            middleware: t.Sequence[Middleware] = None,
            guards: t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]] = None,
            exception_handlers: t.Dict[
                t.Union[int, t.Type[Exception]], t.Callable
            ] = None,
            on_startup: t.Sequence[t.Callable] = None,
            on_shutdown: t.Sequence[t.Callable] = None,
            lifespan: t.Callable[["Starlette"], t.AsyncContextManager] = None,
            config: t.Type[Config] = None,
    ):
        self._injector = StarletteInjector(app=self, root_module=root_module.module)
        _config = config or Config
        self._config = self._injector.create_object(_config)

        super(StarletteApp, self).__init__(
            self._config.DEBUG,
            routes=[],
            middleware=(),
            exception_handlers={},
            on_startup=None,
            on_shutdown=None,
            lifespan=None
        )

        exception_handlers = exception_handlers or {}
        exception_handlers[RequestValidationError] = request_validation_exception_handler
        exception_handlers[APIException] = api_exception_handler

        self._template_folder = self._config.TEMPLATE_FOLDER
        self._root_path = self._config.BASE_DIR
        self._static_folder = self._config.STATIC_FOLDER

        self._module_loaders = [root_module] + root_module.get_modules()

        self._guards = guards or []
        self.router = APIRouter(
            routes, on_startup=on_startup, on_shutdown=on_shutdown,
            lifespan=lifespan, redirect_slashes=self._config.REDIRECT_SLASHES
        )
        self.exception_handlers = exception_handlers
        self.user_middleware = [] if middleware is None else list(middleware)
        self.middleware_stack = self.build_middleware_stack()
        self._process_route_versioning()

        if self.static_files:
            self.router.mount('/static', app=StarletteStaticFiles(directories=self.static_files), name='static')

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

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._guards

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

        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                exception_handlers[key] = value

        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=self._debug)]
            + self.user_middleware
            + [
                Middleware(
                    ExceptionMiddleware, handlers=exception_handlers, debug=self._debug
                ),
                Middleware(RequestVersioningMiddleware, debug=self._debug, config=self.config),
                Middleware(DIRequestServiceProviderMiddleware, debug=self._debug, injector=self.injector),
            ]
        )

        app = self.router
        for cls, options in reversed(middleware):
            app = cls(app=app, **options)
        return app

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        scope["app"] = self
        await self.middleware_stack(scope, receive, send)

    def route(
        self,
        path: str,
        methods: t.List[str] = None,
        name: str = None,
        include_in_schema: bool = True,
    ) -> t.Callable:
        # TODO
        """Override with new configuration"""

    def websocket_route(self, path: str, name: str = None) -> t.Callable:
        # TODO
        """Override with new configuration"""

    def _process_route_versioning(self):
        versioning = self.config.VERSIONING_SCHEME
        if isinstance(versioning, BaseAPIVersioning):
            versioning.modify_routes(self.routes)

    def enable_versioning(
            self, version_type: VERSIONING,
            version_parameter: str = 'version',
            default_version: t.Optional[str] = None,
            **kwargs
    ):
        kwargs.setdefault('version_parameter', version_parameter)
        kwargs.setdefault('default_version', default_version)
        versioning = version_type.value(**kwargs)
        self.config.VERSIONING_SCHEME = versioning
        self._process_route_versioning()
