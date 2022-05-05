import typing as t
from abc import ABC, ABCMeta, abstractmethod

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
)
from ellar.core.events import (
    ApplicationEventHandler,
    ApplicationEventManager,
    EventHandler,
    RouterEventManager,
)
from ellar.core.templating.interface import ModuleTemplating
from ellar.di.injector import Container

from .decorator import class_parameter_executor_wrapper

if t.TYPE_CHECKING:
    from ellar.core.middleware.schema import MiddlewareSchema


class BaseModuleDecorator(ModuleTemplating, ABC, metaclass=ABCMeta):
    def __init__(self) -> None:
        self._routes: t.List[BaseRoute] = []

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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} decorates {self.get_module().__name__}"


def _configure_module(func: t.Callable) -> t.Any:
    def _configure_module_wrapper(self: t.Any, container: Container) -> t.Any:
        _module_decorator = getattr(self, "_module_decorator", None)
        if _module_decorator:
            _module_decorator = t.cast(BaseModuleDecorator, self._module_decorator)
            _module_decorator.configure_module(container=container)
        result = func(self, container=container)
        return result

    return _configure_module_wrapper


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

        for value in namespace.values():
            if hasattr(value, EXCEPTION_HANDLERS_KEY):
                exception_dict: dict = getattr(value, EXCEPTION_HANDLERS_KEY)
                for k, v in exception_dict.items():
                    func = class_parameter_executor_wrapper(cls, v)
                    cls._exceptions_handlers.update({k: func})
            elif hasattr(value, MIDDLEWARE_HANDLERS_KEY):
                middleware: "MiddlewareSchema" = getattr(value, MIDDLEWARE_HANDLERS_KEY)
                middleware.dispatch = class_parameter_executor_wrapper(
                    cls, middleware.dispatch
                )
                cls._middleware.append(middleware.create_middleware())
            elif hasattr(value, ON_APP_INIT):
                on_app_init_event: ApplicationEventHandler = getattr(value, ON_APP_INIT)
                on_app_init_event.handler = class_parameter_executor_wrapper(
                    cls, on_app_init_event.handler
                )
                cls._before_initialisation(on_app_init_event.handler)
            elif hasattr(value, ON_APP_STARTED):
                on_app_started_event: ApplicationEventHandler = getattr(
                    value, ON_APP_STARTED
                )
                on_app_started_event.handler = class_parameter_executor_wrapper(
                    cls, on_app_started_event.handler
                )
                cls._after_initialisation(on_app_started_event.handler)
            elif hasattr(value, ON_SHUTDOWN_KEY):
                on_shutdown_event: EventHandler = getattr(value, ON_SHUTDOWN_KEY)
                on_shutdown_event.handler = class_parameter_executor_wrapper(
                    cls, on_shutdown_event.handler
                )
                cls._on_shutdown(on_shutdown_event.handler)
            elif hasattr(value, ON_STARTUP_KEY):
                on_startup_event: EventHandler = getattr(value, ON_STARTUP_KEY)
                on_startup_event.handler = class_parameter_executor_wrapper(
                    cls, on_startup_event.handler
                )
                cls._on_startup(on_startup_event.handler)

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
