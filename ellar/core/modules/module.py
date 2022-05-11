import inspect
import typing as t
from pathlib import Path

from starlette.middleware import Middleware
from starlette.routing import BaseRoute

from ellar.core.events import ApplicationEventHandler, EventHandler
from ellar.core.guard import GuardCanActivate
from ellar.core.routing import ModuleRouterBase, OperationDefinitions
from ellar.core.routing.controller import ControllerDecorator
from ellar.di import ProviderConfig
from ellar.di.injector import Container

from .base import BaseModuleDecorator, ModuleBase, ModuleBaseMeta


class ModuleData(t.NamedTuple):
    before_init: t.List[ApplicationEventHandler]
    after_init: t.List[ApplicationEventHandler]
    startup_event: t.List[EventHandler]
    shutdown_event: t.List[EventHandler]
    exception_handlers: t.Dict
    middleware: t.List[Middleware]
    routes: t.List[BaseRoute]


class ModuleDecorator(BaseModuleDecorator):
    def __init__(
        self,
        *,
        name: t.Optional[str] = __name__,
        controllers: t.Sequence[ControllerDecorator] = tuple(),
        routers: t.Sequence[
            t.Union[ModuleRouterBase, OperationDefinitions, BaseRoute]
        ] = tuple(),
        services: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[Path, str]] = None,
        static_folder: str = "static",
    ):
        super().__init__()
        self.name = name
        self._controllers = [] if controllers is None else list(controllers)
        self._services: t.List[ProviderConfig] = []
        self._template_folder = template_folder
        self._static_folder = static_folder
        self._module_base_directory = base_directory
        self._module_routers = routers
        self._builder_service(services=services)

    def get_module(self) -> t.Type[ModuleBase]:
        assert self._module_class, "Module not properly configured"
        return self._module_class

    def __call__(self, module_class: t.Type) -> "ModuleDecorator":
        if not self._module_base_directory:
            self._module_base_directory = (
                Path(inspect.getfile(module_class)).resolve().parent
            )
        super(ModuleDecorator, self).__call__(module_class)
        return self

    def configure_module(self, container: Container) -> None:
        for _provider in self._services:
            _provider.register(container)

        for controller in self._controllers:
            ProviderConfig(controller.get_controller_type()).register(container)

    def _builder_service(
        self, services: t.Sequence[t.Union[t.Type, ProviderConfig]]
    ) -> None:
        for item in services:
            if not isinstance(item, ProviderConfig):
                self._services.append(ProviderConfig(item))
                continue
            self._services.append(item)

    def _build_routes(self) -> t.List[BaseRoute]:
        routes = self._get_module_routes()
        for controller in self._controllers:
            routes.extend(controller.build_routes())
        return routes

    def _get_module_routes(
        self,
    ) -> t.List[BaseRoute]:
        results: t.List[BaseRoute] = []
        for item in self._module_routers:
            if isinstance(item, OperationDefinitions) and item.routes:
                results.extend(item.routes)  # type: ignore
                continue
            if isinstance(item, (ModuleRouterBase,)):
                results.extend(item.build_routes())
                continue
            if isinstance(item, (BaseRoute,)):
                results.append(item)
        return results

    def get_module_routers(self) -> t.List[ModuleRouterBase]:
        _module_routers: t.List[ModuleRouterBase] = []

        for controller in self._controllers:
            _module_routers.append(controller.get_mount())

        for item in self._module_routers:
            if isinstance(item, (ModuleRouterBase,)):
                _module_routers.append(item)

        return _module_routers


TAppModuleValue = t.Union[ModuleBase, BaseModuleDecorator]
TAppModule = t.Dict[t.Type[ModuleBase], TAppModuleValue]


class ApplicationModuleDecorator(ModuleDecorator):
    def __init__(
        self,
        *,
        controllers: t.Sequence[ControllerDecorator] = tuple(),
        routers: t.Sequence[
            t.Union[ModuleRouterBase, OperationDefinitions, BaseRoute]
        ] = tuple(),
        services: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
        modules: t.Sequence[
            t.Union[t.Type, BaseModuleDecorator, ModuleBase, t.Type[ModuleBase]]
        ] = tuple(),
        global_guards: t.List[
            t.Union[t.Type[GuardCanActivate], GuardCanActivate]
        ] = None,
        template_folder: t.Optional[str] = None,
        base_directory: t.Optional[t.Union[Path, str]] = None,
        static_folder: str = "static",
    ) -> None:
        super().__init__(
            controllers=controllers,
            services=services,
            template_folder=template_folder,
            base_directory=base_directory,
            static_folder=static_folder,
            routers=routers,
        )
        self._app_modules: t.Sequence[
            t.Union[t.Type, BaseModuleDecorator, ModuleBase, t.Type[ModuleBase]]
        ] = list(modules)
        self._global_guards = global_guards or []

    @property
    def global_guards(
        self,
    ) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    def configure_module(self, container: Container) -> None:
        super().configure_module(container=container)
        for module in self._app_modules:
            container.install(module)

    def build(self) -> ModuleData:
        module_builder = ModuleBuilder(self)

        for module in self._app_modules:
            module_builder.extend(module)

        return module_builder.data

    def get_module_routers(self) -> t.List[ModuleRouterBase]:
        _module_routers = super().get_module_routers()

        for module in self._app_modules:
            if isinstance(module, BaseModuleDecorator):
                _module_routers.extend(module.get_module_routers())

        return _module_routers

    def get_modules_as_dict(self) -> t.Dict[t.Type[ModuleBase], BaseModuleDecorator]:
        _modules: t.List[
            t.Union[ModuleBase, BaseModuleDecorator, t.Type[ModuleBase], t.Type]
        ] = [self]
        _modules.extend(self._app_modules)
        return {
            item.get_module(): item
            for item in _modules
            if isinstance(item, BaseModuleDecorator)
        }


class ModuleBuilder:
    def __init__(
        self, module: t.Union[t.Type[ModuleBase], ModuleBase, BaseModuleDecorator]
    ) -> None:
        self.module = module
        self._data = self.build()

    @property
    def data(self) -> ModuleData:
        return self._data

    @classmethod
    def default(cls) -> ModuleData:
        return ModuleData(
            before_init=[],
            after_init=[],
            startup_event=[],
            shutdown_event=[],
            exception_handlers=dict(),
            middleware=[],
            routes=[],
        )

    def _build_module_base(self, module: t.Type[ModuleBase]) -> ModuleData:
        on_startup_events = list(module.get_on_startup())
        on_shutdown_events = list(module.get_on_shutdown())
        before_init_events = list(module.get_before_initialisation())
        after_init_events = list(module.get_after_initialisation())
        exception_handlers = dict(module.get_exceptions_handlers())
        middleware = list(module.get_middleware())

        return ModuleData(
            before_init=before_init_events,
            after_init=after_init_events,
            startup_event=on_startup_events,
            shutdown_event=on_shutdown_events,
            middleware=middleware,
            exception_handlers=exception_handlers,
            routes=[],
        )

    def _build_module_decorator(self, module: BaseModuleDecorator) -> ModuleData:
        module_data = self._build_module_base(module.get_module())

        return ModuleData(
            before_init=module_data.before_init,
            after_init=module_data.after_init,
            startup_event=module_data.startup_event,
            shutdown_event=module_data.shutdown_event,
            middleware=module_data.middleware,
            exception_handlers=module_data.exception_handlers,
            routes=module.get_routes(),
        )

    def build(self) -> ModuleData:
        if type(self.module) == ModuleBaseMeta:
            return self._build_module_base(type(self.module))

        if isinstance(self.module, ModuleBase):
            module_base = type(self.module).get_module_decorator()
            if module_base:
                return self._build_module_decorator(module_base)
            return self._build_module_base(type(self.module))

        if isinstance(self.module, BaseModuleDecorator):
            return self._build_module_decorator(self.module)

        return self.default()

    def extend(
        self, module: t.Union[t.Type[ModuleBase], ModuleBase, BaseModuleDecorator]
    ) -> None:
        module_data = ModuleBuilder(module)
        self._data.before_init.extend(module_data.data.before_init)
        self._data.after_init.extend(module_data.data.after_init)
        self._data.shutdown_event.extend(module_data.data.shutdown_event)
        self._data.startup_event.extend(module_data.data.startup_event)
        self._data.exception_handlers.update(module_data.data.exception_handlers)
        self._data.middleware.extend(module_data.data.middleware)
        self._data.routes.extend(module_data.data.routes)
