import typing as t
from abc import ABC, abstractmethod

from injector import Module as _InjectorModule
from starlette.middleware import Middleware
from starlette.routing import BaseRoute

from ellar.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    ON_APP_INIT,
    ON_APP_STARTED,
    ON_SHUTDOWN_KEY,
    ON_STARTUP_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.events import (
    ApplicationEventHandler,
    ApplicationEventManager,
    EventHandler,
    RouterEventManager,
)
from ellar.core.routing import ModuleRouterBase
from ellar.core.templating.interface import ModuleTemplating
from ellar.di.injector import Container

from .decorator import class_parameter_executor_wrapper

if t.TYPE_CHECKING:
    from ellar.core.middleware.schema import MiddlewareSchema
    from ellar.core.templating import TemplateFunctionData


class BaseModuleDecorator(ModuleTemplating, ABC):
    template_filter: t.Callable[[str], t.Any]
    template_global: t.Callable[[str], t.Any]

    def __init__(self) -> None:
        self._routes: t.List[BaseRoute] = []
        self._module_class: t.Optional[t.Type[ModuleBase]] = None

    @abstractmethod
    def get_module(self) -> t.Type["ModuleBase"]:
        """decorated module class"""

    @abstractmethod
    def configure_module(self, container: Container) -> None:
        ...

    def get_routes(self, force_build: bool = False) -> t.List[BaseRoute]:
        if not force_build and self._routes:
            return self._routes
        self._routes = self._build_routes()
        return self._routes

    @abstractmethod
    def _build_routes(self) -> t.List[BaseRoute]:
        """build module controller routes"""

    @abstractmethod
    def get_module_routers(self) -> t.List[ModuleRouterBase]:
        """gets ModuleRouterBase"""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} decorates {self.get_module().__name__}"

    def __call__(self, module_class: t.Type) -> "BaseModuleDecorator":
        _module_class = t.cast(t.Type[ModuleBase], module_class)
        attr: t.Dict = {
            item: getattr(_module_class, item)
            for item in dir(_module_class)
            if "__" not in item
        }

        if type(_module_class) != ModuleBaseMeta:
            attr.update(_module_decorator=self)
            _module_class = type(
                module_class.__name__,
                (module_class, ModuleBase),
                attr,
            )
        _module_class._module_decorator = self
        self._module_class = _module_class
        ModuleBaseBuilder(_module_class).build(attr)
        return self


def _configure_module(func: t.Callable) -> t.Any:
    def _configure_module_wrapper(self: t.Any, container: Container) -> t.Any:
        _module_decorator = getattr(self, "_module_decorator", None)
        if _module_decorator:
            _module_decorator = t.cast(BaseModuleDecorator, self._module_decorator)
            _module_decorator.configure_module(container=container)
        result = func(self, container=container)
        return result

    return _configure_module_wrapper


class ModuleBaseBuilder:
    __slots__ = ("_cls", "_actions")

    def __init__(self, cls: t.Union[t.Type["ModuleBase"], "ModuleBaseMeta"]) -> None:
        self._cls = cls
        self._actions: t.Dict[str, t.Callable[[t.Any], None]] = dict()
        self._actions.update(
            {
                EXCEPTION_HANDLERS_KEY: self.exception_config,
                MIDDLEWARE_HANDLERS_KEY: self.middleware_config,
                ON_APP_INIT: self.on_app_init_config,
                ON_APP_STARTED: self.on_app_started_config,
                ON_SHUTDOWN_KEY: self.on_shut_down_config,
                ON_STARTUP_KEY: self.on_startup_config,
                TEMPLATE_GLOBAL_KEY: self.template_global_config,
                TEMPLATE_FILTER_KEY: self.template_filter_config,
            },
        )

    def exception_config(self, exception_dict: t.Dict) -> None:
        for k, v in exception_dict.items():
            func = class_parameter_executor_wrapper(self._cls, v)
            self._cls.get_exceptions_handlers().update({k: func})

    @t.no_type_check
    def middleware_config(self, middleware: "MiddlewareSchema") -> None:
        middleware.dispatch = class_parameter_executor_wrapper(
            self._cls, middleware.dispatch
        )
        self._cls.get_middleware().append(middleware.create_middleware())

    def on_app_init_config(self, on_app_init_event: ApplicationEventHandler) -> None:
        on_app_init_event.handler = class_parameter_executor_wrapper(
            self._cls, on_app_init_event.handler
        )
        self._cls.get_before_initialisation()(on_app_init_event.handler)

    def on_app_started_config(
        self, on_app_started_event: ApplicationEventHandler
    ) -> None:
        on_app_started_event.handler = class_parameter_executor_wrapper(
            self._cls, on_app_started_event.handler
        )
        self._cls.get_after_initialisation()(on_app_started_event.handler)

    def on_shut_down_config(self, on_shutdown_event: EventHandler) -> None:
        on_shutdown_event.handler = class_parameter_executor_wrapper(
            self._cls, on_shutdown_event.handler
        )
        self._cls.get_on_shutdown()(on_shutdown_event.handler)

    def on_startup_config(self, on_startup_event: EventHandler) -> None:
        on_startup_event.handler = class_parameter_executor_wrapper(
            self._cls, on_startup_event.handler
        )
        self._cls.get_on_startup()(on_startup_event.handler)

    def template_filter_config(self, template_filter: "TemplateFunctionData") -> None:
        module_decorator = self._cls.get_module_decorator()
        if module_decorator:
            module_decorator.jinja_environment.filters[
                template_filter.name
            ] = class_parameter_executor_wrapper(self._cls, template_filter.func)

    def template_global_config(self, template_filter: "TemplateFunctionData") -> None:
        module_decorator = self._cls.get_module_decorator()
        if module_decorator:
            module_decorator.jinja_environment.globals[
                template_filter.name
            ] = class_parameter_executor_wrapper(self._cls, template_filter.func)

    def build(self, namespace: t.Dict) -> None:
        for item in namespace.values():
            for k, func in self._actions.items():
                if hasattr(item, k):
                    value = getattr(item, k)
                    func(value)


class ModuleBaseMeta(type):
    _module_decorator: t.Optional[BaseModuleDecorator]

    _on_startup: RouterEventManager
    _on_shutdown: RouterEventManager

    _before_initialisation: ApplicationEventManager
    _after_initialisation: ApplicationEventManager

    _exceptions_handlers: t.Dict
    _middleware: t.List[Middleware]

    @t.no_type_check
    def __init__(cls, name, bases, namespace) -> None:
        super().__init__(name, bases, namespace)
        cls._module_decorator = namespace.get("_module_decorator", None)

        cls._on_startup = RouterEventManager()
        cls._on_shutdown = RouterEventManager()

        cls._before_initialisation = ApplicationEventManager()
        cls._after_initialisation = ApplicationEventManager()

        cls._exceptions_handlers = dict()
        cls._middleware = []

    def get_module_decorator(cls) -> t.Optional["BaseModuleDecorator"]:
        return cls._module_decorator

    def get_on_startup(cls) -> RouterEventManager:
        return cls._on_startup

    def get_on_shutdown(cls) -> RouterEventManager:
        return cls._on_shutdown

    def get_before_initialisation(cls) -> ApplicationEventManager:
        return cls._before_initialisation

    def get_after_initialisation(cls) -> ApplicationEventManager:
        return cls._after_initialisation

    def get_exceptions_handlers(
        cls,
    ) -> t.Dict[t.Union[int, t.Type[Exception]], t.Callable]:
        return cls._exceptions_handlers

    def get_middleware(cls) -> t.List[Middleware]:
        return cls._middleware


class ModuleBase(_InjectorModule, metaclass=ModuleBaseMeta):
    def register_services(self, container: Container) -> None:
        """Register other services manually"""

    @_configure_module
    def configure(self, container: Container) -> None:
        self.register_services(container=container)
