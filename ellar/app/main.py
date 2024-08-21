import json
import logging
import logging.config
import typing as t

from ellar.auth.handlers import AuthenticationHandlerType
from ellar.common import (
    IHostContextFactory,
    constants,
)
from ellar.common.datastructures import State, URLPath
from ellar.common.interfaces import IExceptionHandler, IExceptionMiddlewareService
from ellar.common.models import EllarInterceptor, GuardCanActivate
from ellar.common.templating import Environment, ModuleTemplating
from ellar.common.types import ASGIApp, TReceive, TScope, TSend
from ellar.core import HttpRequestConnectionContext, Request
from ellar.core.conf import Config
from ellar.core.exceptions.service import EXCEPTION_DEFAULT_EXCEPTION_HANDLERS
from ellar.core.execution_context import injector_context
from ellar.core.middleware import (
    Middleware as EllarMiddleware,
)
from ellar.core.routing import ApplicationRouter, AppStaticFileMount
from ellar.core.services import Reflector, reflector
from ellar.core.versioning import BaseAPIVersioning, VersioningSchemes
from ellar.di import EllarInjector, ProviderConfig
from ellar.threading import run_as_sync
from jinja2 import Environment as JinjaEnvironment
from jinja2 import pass_context
from starlette.datastructures import URL
from starlette.routing import BaseRoute

from .context import (
    enable_versioning,
    ensure_available_in_providers,
    use_authentication_schemes,
    use_exception_handler,
    use_global_guards,
    use_global_interceptors,
)
from .lifespan import EllarApplicationLifespan

logger = logging.getLogger("ellar")


class App:
    def __init__(
        self,
        config: "Config",
        injector: EllarInjector,
        routes: t.Optional[t.List[BaseRoute]] = None,
        lifespan: t.Optional[t.Callable[["App"], t.AsyncContextManager]] = None,
    ):
        _routes = routes or []
        assert isinstance(config, Config), "config must instance of Config"
        assert isinstance(
            injector, EllarInjector
        ), "injector must instance of EllarInjector"

        self._config = config
        self._injector: EllarInjector = injector

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
            else constants.LOG_LEVELS.info.value
        )
        logger_ellar = logging.getLogger("ellar")
        logger_ellar_request = logging.getLogger("ellar.request")
        logger_ellar_di = logging.getLogger("ellar.di")

        if not logger_ellar.handlers:
            formatter = logging.Formatter(constants.ELLAR_LOG_FMT_STRING)
            stream_handler = logging.StreamHandler()
            # file_handler = logging.FileHandler("my_app.log")
            # file_handler.setFormatter(formatter)
            # logger_.addHandler(file_handler)
            stream_handler.setFormatter(formatter)

            logger_ellar.addHandler(stream_handler)
            logger_ellar_request.addHandler(stream_handler)
            logger_ellar_di.addHandler(stream_handler)

        logger_ellar.setLevel(log_level)
        logger_ellar_request.setLevel(log_level)
        logger_ellar_di.setLevel(log_level)

    def get_guards(self) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self.config.GLOBAL_GUARDS

    def get_interceptors(
        self,
    ) -> t.List[t.Union[EllarInterceptor, t.Type[EllarInterceptor]]]:
        return self.config.GLOBAL_INTERCEPTORS

    @run_as_sync
    @t.no_type_check
    async def use_global_guards(
        self, *guards: t.Union["GuardCanActivate", t.Type["GuardCanActivate"]]
    ) -> None:
        async with self.with_injector_context():
            use_global_guards(*guards)

    @run_as_sync
    @t.no_type_check
    async def use_global_interceptors(
        self, *interceptors: t.Union[EllarInterceptor, t.Type[EllarInterceptor]]
    ) -> None:
        async with self.with_injector_context():
            use_global_interceptors(*interceptors)

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

    def build_middleware_stack(self) -> ASGIApp:
        self.injector.get(IExceptionMiddlewareService).build_exception_handlers(
            *EXCEPTION_DEFAULT_EXCEPTION_HANDLERS, *list(self.config.EXCEPTION_HANDLERS)
        )

        app = self.router
        for cls, args, kwargs in reversed(
            t.cast(t.List[EllarMiddleware], self.config.MIDDLEWARE)
        ):
            try:
                app = cls(app, *args, **kwargs)
            except Exception as ex:
                logger.exception(ex, f"Unable to setup middleware='{cls}'")
                raise ex
        return app

    def request_context(
        self,
        scope: TScope,
        receive: TReceive = constants.empty_receive,
        send: TSend = constants.empty_send,
    ) -> HttpRequestConnectionContext:
        """
        Create an RequestContext during request and provides instance for `current_connection`.
        e.g

        request = current_connection.switch_http_connection().get_request()
        websocket = current_connection.switch_to_websocket().get_client()
        """
        context_factory = self.injector.get(IHostContextFactory)
        return HttpRequestConnectionContext(
            host_context=context_factory.create_context(scope, receive, send)
        )

    @t.no_type_check
    def with_injector_context(self) -> t.AsyncGenerator[EllarInjector, t.Any]:
        return injector_context(self.injector)

    @t.no_type_check
    async def __call__(self, scope: TScope, receive: TReceive, send: TSend) -> None:
        lifespan = scope["type"] == "lifespan"
        scope["app"] = self

        async with self.with_injector_context():
            if self.middleware_stack is None:
                self.middleware_stack = self.build_middleware_stack()

                if (
                    self.config.STATIC_MOUNT_PATH
                    and self.config.STATIC_MOUNT_PATH not in self.router.routes
                ):
                    self.router.add(AppStaticFileMount(self))

            if lifespan:
                return await self.middleware_stack(scope, receive, send)

            ## setup request_scope context
            async with self.request_context(scope, receive, send):
                return await self.middleware_stack(scope, receive, send)

    @property
    def routes(self) -> t.List[BaseRoute]:
        return self.router.routes.get_routes()

    def url_path_for(self, name: str, **path_params: t.Any) -> URLPath:
        return self.router.url_path_for(name, **path_params)

    @run_as_sync
    @t.no_type_check
    async def enable_versioning(
        self,
        schema: VersioningSchemes,
        version_parameter: str = "version",
        default_version: t.Optional[str] = None,
        **init_kwargs: t.Any,
    ) -> None:
        async with self.with_injector_context():
            enable_versioning(
                schema,
                version_parameter=version_parameter,
                default_version=default_version,
                **init_kwargs,
            )

    @run_as_sync
    @t.no_type_check
    async def _finalize_app_initialization(self) -> None:
        async with self.with_injector_context():
            self.injector.owner.add_provider(
                ProviderConfig(App, use_value=self, tag=self.__class__.__name__)
            )
            ensure_available_in_providers(*self.get_guards())
            ensure_available_in_providers(*self.get_interceptors())
            ensure_available_in_providers(*self.config.EXCEPTION_HANDLERS)

            ensure_available_in_providers(
                *[
                    item.cls
                    for item in self.config.MIDDLEWARE
                    if isinstance(item, EllarMiddleware)
                ]
            )
            # self.injector.owner.add_provider(
            #     GLOBAL_CONTROLLER_CLASS, export=True
            # )

    @run_as_sync
    @t.no_type_check
    async def add_exception_handler(
        self,
        *exception_handlers: IExceptionHandler,
    ) -> None:
        async with self.with_injector_context():
            use_exception_handler(*exception_handlers)

    @property
    def reflector(self) -> Reflector:
        return reflector

    @run_as_sync
    @t.no_type_check
    async def add_authentication_schemes(
        self, *authentication: AuthenticationHandlerType
    ) -> None:
        async with self.with_injector_context():
            use_authentication_schemes(*authentication)

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
        def url_for(context: t.Dict, name: str, **path_params: t.Any) -> URL:
            request = t.cast(Request, context["request"])
            return request.url_for(name, **path_params)

        jinja_env = Environment(self, **jinja_options)
        jinja_env.globals.update(url_for=url_for, config=self._config)
        jinja_env.policies["json.dumps_function"] = json.dumps

        # jinja_env.policies["get_messages"] = get_messages
        jinja_env.globals.update(self._config.get(constants.TEMPLATE_GLOBAL_KEY, {}))
        jinja_env.filters.update(self._config.get(constants.TEMPLATE_FILTER_KEY, {}))

        self.config.APP_CONTEXT_PROCESSORS = list(
            self.config.TEMPLATES_CONTEXT_PROCESSORS
        )
        return jinja_env

    def setup_jinja_environment(self) -> Environment:
        """Sets up Jinja2 Environment and adds it to DI"""
        jinja_environment = self._create_jinja_environment()

        self.injector.tree_manager.get_app_module().add_provider(
            ProviderConfig(Environment, use_value=jinja_environment), export=True
        )
        self.injector.tree_manager.get_app_module().add_provider(
            ProviderConfig(JinjaEnvironment, use_value=jinja_environment), export=True
        )
        return jinja_environment
