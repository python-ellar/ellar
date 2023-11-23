import logging
import logging.config
import typing as t

from ellar.app.context import ApplicationContext
from ellar.auth.handlers import AuthenticationHandlerType
from ellar.common import GlobalGuard, IIdentitySchemes
from ellar.common.compatible import cached_property
from ellar.common.constants import ELLAR_LOG_FMT_STRING, LOG_LEVELS
from ellar.common.datastructures import State, URLPath
from ellar.common.interfaces import IExceptionHandler, IExceptionMiddlewareService
from ellar.common.models import EllarInterceptor, GuardCanActivate
from ellar.common.templating import Environment
from ellar.common.types import ASGIApp, T, TReceive, TScope, TSend
from ellar.core import reflector
from ellar.core.conf import Config
from ellar.core.middleware import (
    CORSMiddleware,
    ExceptionMiddleware,
    Middleware,
    RequestServiceProviderMiddleware,
    RequestVersioningMiddleware,
    SessionMiddleware,
    TrustedHostMiddleware,
)
from ellar.core.middleware.authentication import IdentityMiddleware
from ellar.core.modules import (
    DynamicModule,
    ModuleBase,
    ModuleRefBase,
    ModuleSetup,
    ModuleTemplateRef,
)
from ellar.core.routing import ApplicationRouter
from ellar.core.services import Reflector
from ellar.core.versioning import BaseAPIVersioning, VersioningSchemes
from ellar.di import EllarInjector
from starlette.routing import BaseRoute, Mount

from .lifespan import EllarApplicationLifespan
from .mixin import AppMixin


class App(AppMixin):
    def __init__(
        self,
        config: "Config",
        injector: EllarInjector,
        lifespan: t.Optional[t.Callable[["App"], t.AsyncContextManager]] = None,
        global_guards: t.Optional[
            t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]
        ] = None,
    ):
        assert isinstance(config, Config), "config must instance of Config"
        assert isinstance(
            injector, EllarInjector
        ), "injector must instance of EllarInjector"

        self._config = config
        self._injector: EllarInjector = injector

        self._global_guards = [] if global_guards is None else list(global_guards)
        self._global_interceptors: t.List[
            t.Union[EllarInterceptor, t.Type[EllarInterceptor]]
        ] = []
        self._exception_handlers = list(self.config.EXCEPTION_HANDLERS)

        self._user_middleware = list(t.cast(list, self.config.MIDDLEWARE))

        self._static_app: t.Optional[ASGIApp] = None

        self.state = State()
        self.config.DEFAULT_LIFESPAN_HANDLER = (
            lifespan or self.config.DEFAULT_LIFESPAN_HANDLER
        )
        self.router = ApplicationRouter(
            routes=self._get_module_routes(),
            redirect_slashes=self.config.REDIRECT_SLASHES,
            default=self.config.DEFAULT_NOT_FOUND_HANDLER,
            lifespan=EllarApplicationLifespan(
                self.config.DEFAULT_LIFESPAN_HANDLER  # type: ignore[arg-type]
            ).lifespan,
        )
        self._finalize_app_initialization()
        self.middleware_stack = self.build_middleware_stack()
        self._config_logging()

    def _config_logging(self) -> None:
        log_level = (
            self.config.LOG_LEVEL.value
            if self.config.LOG_LEVEL
            else LOG_LEVELS.info.value
        )
        logger_ = logging.getLogger("ellar")
        if not logger_.handlers:
            formatter = logging.Formatter(ELLAR_LOG_FMT_STRING)
            stream_handler = logging.StreamHandler()
            # file_handler = logging.FileHandler("my_app.log")
            # file_handler.setFormatter(formatter)
            # logger_.addHandler(file_handler)
            stream_handler.setFormatter(formatter)
            logger_.addHandler(stream_handler)

            logger_.setLevel(log_level)
        else:
            logging.getLogger("ellar").setLevel(log_level)
            logging.getLogger("ellar.request").setLevel(log_level)

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
            _routes.extend(module_ref.routes)

        return _routes

    def install_module(
        self,
        module: t.Union[t.Type[T], t.Type[ModuleBase], DynamicModule],
        **init_kwargs: t.Any,
    ) -> t.Union[T, ModuleBase]:
        if isinstance(module, DynamicModule):
            module.apply_configuration()
            module_config = ModuleSetup(module.module, init_kwargs=init_kwargs)
        else:
            module_config = ModuleSetup(module, init_kwargs=init_kwargs)

        module_ref = self.injector.get_module(module_config.module)
        if module_ref:
            return module_ref.get_module_instance()

        module_ref = module_config.get_module_ref(  # type: ignore[assignment]
            config=self.config,
            container=self.injector.container,
        )
        assert isinstance(module_ref, ModuleRefBase)
        self.injector.add_module(module_ref)

        module_ref.run_module_register_services()
        if isinstance(module_ref, ModuleTemplateRef):
            self.router.extend(module_ref.routes)
            self.reload_static_app()

        self.rebuild_middleware_stack()

        return t.cast(T, module_ref.get_module_instance())

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self.__global_guard + self._global_guards

    def get_interceptors(
        self,
    ) -> t.List[t.Union[EllarInterceptor, t.Type[EllarInterceptor]]]:
        return self._global_interceptors

    def use_global_guards(
        self, *guards: t.Union["GuardCanActivate", t.Type["GuardCanActivate"]]
    ) -> None:
        self._global_guards.extend(guards)

    def use_global_interceptors(
        self, *interceptors: t.Union[EllarInterceptor, t.Type[EllarInterceptor]]
    ) -> None:
        self._global_interceptors.extend(interceptors)

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
    def config(self) -> "Config":
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
                    TrustedHostMiddleware,
                    allowed_hosts=allowed_hosts,
                    www_redirect=self.config.REDIRECT_HOST,
                ),
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
                    RequestServiceProviderMiddleware,
                    debug=self.debug,
                    handler=error_handler,
                ),
                Middleware(
                    RequestVersioningMiddleware,
                    debug=self.debug,
                ),
                Middleware(
                    SessionMiddleware,
                ),
                Middleware(
                    IdentityMiddleware,
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
        for item in reversed(middleware):
            app = item(app=app, injector=self.injector)
        return app

    def application_context(self) -> ApplicationContext:
        """
        Create an ApplicationContext.
        Use as a contextmanager block to make `current_app`, `current_injector` and `current_config` point at this application.

        It can be used manually outside ellar cli commands or request,
        e.g.,
        with app.application_context():
            assert current_app is app
            run_some_actions()
        """
        return ApplicationContext.create(app=self)

    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        with self.application_context() as ctx:
            scope["app"] = ctx.app
            await self.middleware_stack(scope, receive, send)

    @property
    def routes(self) -> t.List[BaseRoute]:
        return self.router.routes.get_routes()

    def url_path_for(self, name: str, **path_params: t.Any) -> URLPath:
        return self.router.url_path_for(name, **path_params)

    def enable_versioning(
        self,
        schema: VersioningSchemes,
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
        self.injector.container.register_instance(self)
        self.injector.container.register_instance(self.config, Config)
        self.injector.container.register_instance(self.jinja_environment, Environment)
        self.injector.container.register_instance(self.jinja_environment, Environment)

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

    @property
    def reflector(self) -> Reflector:
        return reflector

    @cached_property
    def __identity_scheme(self) -> IIdentitySchemes:
        return self.injector.get(IIdentitySchemes)  # type: ignore[no-any-return]

    @cached_property
    def __global_guard(
        self,
    ) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        try:
            guard = self.injector.get(GlobalGuard)
            return [guard]
        except Exception:
            return []

    def add_authentication_schemes(
        self, *authentication: AuthenticationHandlerType
    ) -> None:
        for auth in authentication:
            self.__identity_scheme.add_authentication(auth)
