import typing as t

from injector import Module as _InjectorModule
from starlette.middleware import Middleware

from ellar.core.events import ApplicationEventManager, RouterEventManager
from ellar.di.injector import Container

if t.TYPE_CHECKING:  # pragma: no cover
    from .decorator.base import BaseModuleDecorator


def _configure_module(func: t.Callable) -> t.Any:
    def _configure_module_wrapper(self: t.Any, container: Container) -> t.Any:
        _module_decorator: "BaseModuleDecorator" = t.cast(
            "BaseModuleDecorator", getattr(self, "_module_decorator", None)
        )
        if _module_decorator:
            _module_decorator.configure_module(container=container)
        result = func(self, container=container)
        return result

    return _configure_module_wrapper


class ModuleBaseMeta(type):
    _module_decorator: t.Optional["BaseModuleDecorator"]

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
