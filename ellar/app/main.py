import json
import logging
import logging.config
import typing as t

from ellar.auth.handlers import AuthenticationHandlerType
from ellar.auth.middleware import IdentityMiddleware, SessionMiddleware
from ellar.common import (
    GlobalGuard,
    IHostContext,
    IHostContextFactory,
    IIdentitySchemes,
)
from ellar.common.compatible import cached_property
from ellar.common.constants import (
    ELLAR_LOG_FMT_STRING,
    LOG_LEVELS,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.common.datastructures import State, URLPath
from ellar.common.interfaces import IExceptionHandler, IExceptionMiddlewareService
from ellar.common.models import EllarInterceptor, GuardCanActivate
from ellar.common.templating import Environment, ModuleTemplating
from ellar.common.types import ASGIApp, TReceive, TScope, TSend
from ellar.core.conf import Config
from ellar.core.connection import Request
from ellar.core.context import ApplicationContext
from ellar.core.middleware import (
    CORSMiddleware,
    ExceptionMiddleware,
    RequestVersioningMiddleware,
    ServerErrorMiddleware,
    TrustedHostMiddleware,
)
from ellar.core.middleware import (
    Middleware as EllarMiddleware,
)
from ellar.core.routing import ApplicationRouter, AppStaticFileMount
from ellar.core.services import Reflector, reflector
from ellar.core.versioning import BaseAPIVersioning, VersioningSchemes
from ellar.di import EllarInjector, ProviderConfig, is_decorated_with_injectable
from ellar.di.injector.tree_manager import TreeData
from jinja2 import Environment as JinjaEnvironment
from jinja2 import pass_context
from starlette.datastructures import URL
from starlette.routing import BaseRoute

from .lifespan import EllarApplicationLifespan


class App:
    def __init__(
        self,
        config: "Config",
        injector: EllarInjector,
        routes: t.Optional[t.List[BaseRoute]] = None,
        lifespan: t.Optional[t.Callable[["App"], t.AsyncContextManager]] = None,
        global_guards: t.Optional[
            t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]
        ] = None,
    ):
        _routes = routes or []
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
        self.config.setdefault("EXCEPTION_HANDLERS", [])
        self.config.setdefault("MIDDLEWARE", [])

        self.state = State()
        self.config.DEFAULT_LIFESPAN_HANDLER = (
            lifespan or self.config.DEFAULT_LIFESPAN_HANDLER
        )

        self.router = ApplicationRouter(
            routes=_routes,
            redirect_slashes=self.config.REDIRECT_SLASHES,
            default=self.config.DEFAULT_NOT_FOUND_HANDLER,
            lifespan=EllarApplicationLifespan(
                self.config.DEFAULT_LIFESPAN_HANDLER  # type: ignore[arg-type]
            ).lifespan,
        )

        self._finalize_app_initialization()
        self.middleware_stack: t.Optional[ASGIApp] = None
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
        self._ensure_available_in_providers(*guards)

    def use_global_interceptors(
        self, *interceptors: t.Union[EllarInterceptor, t.Type[EllarInterceptor]]
    ) -> None:
        self._global_interceptors.extend(interceptors)
        self._ensure_available_in_providers(*interceptors)

    @property
    def injector(self) -> EllarInjector:
        return self._injector

    @property
    def versioning_scheme(self) -> BaseAPIVersioning:
        return t.cast(BaseAPIVersioning, self._config.VERSIONING_SCHEME)

    @property
    def config(self) -> "Config":
        return self._config

    @property
    def debug(self) -> bool:
        return self._config.DEBUG

    @debug.setter
    def debug(self, value: bool) -> None:
        self._config.DEBUG = value
        # TODO: Add warning
        # self.rebuild_stack()

    def _ensure_available_in_providers(self, *items: t.Any) -> None:
        def _predicate(item_: t.Type) -> t.Callable:
            def _(data: TreeData) -> bool:
                return item_ in data.exports or item_ in data.providers

            return _

        for item in items:
            if isinstance(item, type) and is_decorated_with_injectable(item):
                module = next(
                    self.injector.tree_manager.find_module(predicate=_predicate(item))
                )
                if not module:
                    self.injector.tree_manager.get_root_module().add_provider(
                        provider=item, export=True
                    )
                    # self.injector.module_info.ref.add_provider(
                    #     provider=item, export=True
                    # )

    def build_middleware_stack(self) -> ASGIApp:
        service_middleware = self.injector.get(IExceptionMiddlewareService)
        service_middleware.build_exception_handlers(
            *list(self.config.EXCEPTION_HANDLERS)
        )

        error_handler = service_middleware.get_500_error_handler()
        allowed_hosts = self.config.ALLOWED_HOSTS

        if self.debug and allowed_hosts != ["*"]:
            allowed_hosts = ["*"]

        user_middlewares = (
            list(self.config.MIDDLEWARE) if self.config.MIDDLEWARE else []
        )
        middleware = (
            [
                EllarMiddleware(
                    TrustedHostMiddleware,
                    allowed_hosts=allowed_hosts,
                    www_redirect=self.config.REDIRECT_HOST,
                ),
                EllarMiddleware(
                    CORSMiddleware,
                    allow_origins=self.config.CORS_ALLOW_ORIGINS,
                    allow_credentials=self.config.CORS_ALLOW_CREDENTIALS,
                    allow_methods=self.config.CORS_ALLOW_METHODS,
                    allow_headers=self.config.CORS_ALLOW_HEADERS,
                    allow_origin_regex=self.config.CORS_ALLOW_ORIGIN_REGEX,
                    expose_headers=self.config.CORS_EXPOSE_HEADERS,
                    max_age=self.config.CORS_MAX_AGE,
                ),
                EllarMiddleware(
                    ServerErrorMiddleware,
                    debug=self.debug,
                    handler=error_handler,
                ),
                EllarMiddleware(
                    RequestVersioningMiddleware,
                    debug=self.debug,
                ),
                EllarMiddleware(
                    SessionMiddleware,
                ),
                EllarMiddleware(
                    IdentityMiddleware,
                ),
            ]
            + user_middlewares
            + [
                EllarMiddleware(
                    ExceptionMiddleware,
                    exception_middleware_service=service_middleware,
                    debug=self.debug,
                ),
            ]
        )

        app = self.router
        for cls, args, kwargs in reversed(middleware):
            app = cls(app, *args, **kwargs)
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
        async with self.application_context() as context:
            scope["app"] = self

            async with context.injector.create_asgi_args() as service_provider:
                context_factory = service_provider.get(IHostContextFactory)
                service_provider.update_scoped_context(
                    IHostContext, context_factory.create_context(scope)
                )

                if self.middleware_stack is None:
                    self.middleware_stack = self.build_middleware_stack()

                    if (
                        self.config.STATIC_MOUNT_PATH
                        and self.config.STATIC_MOUNT_PATH not in self.router.routes
                    ):
                        self.router.add_route(AppStaticFileMount(self))

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
        self._ensure_available_in_providers(*self._global_guards)
        self._ensure_available_in_providers(*self._global_interceptors)
        self._ensure_available_in_providers(*self.config.EXCEPTION_HANDLERS)
        self._ensure_available_in_providers(
            *[
                item.cls
                for item in self.config.MIDDLEWARE
                if isinstance(item, EllarMiddleware)
            ]
        )
        self.injector.owner.add_provider(
            ProviderConfig(App, use_value=self, tag=self.__class__.__name__)
        )

    def add_exception_handler(
        self,
        *exception_handlers: IExceptionHandler,
    ) -> None:
        # _added_any = False
        for exception_handler in exception_handlers:
            if exception_handler not in self.config.EXCEPTION_HANDLERS:
                self.config.EXCEPTION_HANDLERS.append(exception_handler)
                self._ensure_available_in_providers(exception_handler)

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
            if guard.__class__.__name__ == "GlobalCanActivatePlaceHolder":
                return []

            return [guard]
        except Exception:
            return []

    def add_authentication_schemes(
        self, *authentication: AuthenticationHandlerType
    ) -> None:
        for auth in authentication:
            self.__identity_scheme.add_authentication(auth)
            self._ensure_available_in_providers(auth)

    def get_module_loaders(self) -> t.Generator[ModuleTemplating, None, None]:
        for loader in self._injector.get_templating_modules().values():
            yield loader

    def _create_jinja_environment(self) -> Environment:
        # TODO: rename to `create_jinja_environment`
        def select_jinja_auto_escape(filename: str) -> bool:
            if filename is None:  # pragma: no cover
                return True
            return filename.endswith((".html", ".htm", ".xml", ".xhtml"))

        options_defaults: t.Dict = {
            "extensions": [],
            "auto_reload": self.debug,
            "autoescape": select_jinja_auto_escape,
        }
        jinja_options: t.Dict = t.cast(
            t.Dict, self._config.JINJA_TEMPLATES_OPTIONS or {}
        )

        for k, v in options_defaults.items():
            jinja_options.setdefault(k, v)

        @pass_context
        def url_for(context: dict, name: str, **path_params: t.Any) -> URL:
            request = t.cast(Request, context["request"])
            return request.url_for(name, **path_params)

        jinja_env = Environment(self, **jinja_options)
        jinja_env.globals.update(
            url_for=url_for,
            config=self._config,
        )
        jinja_env.policies["json.dumps_function"] = json.dumps
        # jinja_env.policies["get_messages"] = get_messages

        jinja_env.globals.update(self._config.get(TEMPLATE_GLOBAL_KEY, {}))
        jinja_env.filters.update(self._config.get(TEMPLATE_FILTER_KEY, {}))

        return jinja_env

    def setup_jinja_environment(self) -> Environment:
        """Sets up Jinja2 Environment and adds it to DI"""
        jinja_environment = self._create_jinja_environment()

        self.injector.tree_manager.get_root_module().add_provider(
            ProviderConfig(Environment, use_value=jinja_environment), export=True
        )
        self.injector.tree_manager.get_root_module().add_provider(
            ProviderConfig(JinjaEnvironment, use_value=jinja_environment), export=True
        )
        return jinja_environment
