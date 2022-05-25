import inspect
import typing as t
from pathlib import Path

from starlette.routing import BaseRoute, Mount

from ellar.core.guard import GuardCanActivate
from ellar.core.routing import ModuleRouterBase
from ellar.core.routing.controller import ControllerDecorator
from ellar.di import ProviderConfig
from ellar.di.injector import Container
from ellar.exceptions import ImproperConfiguration

from ..base import ModuleBase, ModuleBaseMeta
from ..builder import ModuleBaseBuilder
from ..schema import ModuleData
from .base import BaseModuleDecorator
from .builder import ModuleDecoratorBuilder


class ModuleDecorator(BaseModuleDecorator):
    __slots__ = (
        "_routes",
        "_module_class",
        "name",
        "_controllers",
        "_services",
        "_template_folder",
        "_static_folder",
        "_module_base_directory",
        "_module_routers",
    )

    def __init__(
        self,
        *,
        name: t.Optional[str] = __name__,
        controllers: t.Sequence[t.Union[ControllerDecorator, t.Type]] = tuple(),
        routers: t.Sequence[t.Union[ModuleRouterBase, Mount]] = tuple(),
        services: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
        template_folder: t.Optional[str] = "templates",
        base_directory: t.Optional[t.Union[Path, str]] = None,
        static_folder: str = "static",
    ):
        super().__init__()
        self.name = name
        self._routes: t.List[BaseRoute] = []
        self._controllers = [] if controllers is None else list(controllers)
        self._services: t.List[ProviderConfig] = []
        self._template_folder = template_folder
        self._static_folder = static_folder
        self._module_base_directory = base_directory
        self._module_routers = routers
        self._module_class = None
        self._builder_service(services=services)

    def __repr__(self) -> str:
        if not self._module_class:  # pragma: no cover
            return f"< @{self.__class__.__name__}(NOT DEFINED) >"
        return f"< @{self.__class__.__name__}({self.get_module().__name__}) >"

    def validate_module_decorator(self) -> None:
        self._validate_controllers()
        self._validate_module_routers()
        if not self._module_class:
            raise ImproperConfiguration(
                "ModuleDecorator is not used properly. It has to decorate a class"
            )

    def _validate_controllers(self) -> None:
        for controller in self._controllers:
            if not isinstance(controller, ControllerDecorator):
                raise ImproperConfiguration(
                    f"Registered Controller is an invalid Controller Object. {controller}"
                )

    def _validate_module_routers(self) -> None:
        for router in self._module_routers:
            if not isinstance(router, (ModuleRouterBase, Mount)):
                raise ImproperConfiguration(
                    f"Registered Router is an invalid Router. {router}"
                )

    def get_module(self) -> t.Type[ModuleBase]:
        assert self._module_class, "ModuleDecorator not properly configured"
        return self._module_class

    def __call__(self, module_class: t.Type) -> "ModuleDecorator":
        if not self._module_base_directory:
            self._module_base_directory = (
                Path(inspect.getfile(module_class)).resolve().parent
            )

        _module_class = t.cast(t.Type["ModuleBase"], module_class)
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
        else:
            _module_class._module_decorator = self
        ModuleBaseBuilder(_module_class).build(attr)

        self._module_class = _module_class
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
            provider = item
            if not isinstance(item, ProviderConfig):
                provider = ProviderConfig(item)
            self._services.append(t.cast(ProviderConfig, provider))

    def get_routes(self) -> t.List[BaseRoute]:
        if not self._routes:
            self._routes = self._build_routes()
        return self._routes

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
            if isinstance(item, (ModuleRouterBase,)):
                results.extend(item.build_routes())
                continue
            if isinstance(item, (Mount,)):
                results.append(item)
        return results

    def get_module_routers(self) -> t.List[ModuleRouterBase]:
        _module_routers: t.List[ModuleRouterBase] = []

        for controller in self._controllers:
            _module_routers.append(controller.get_router())

        for item in self._module_routers:
            if isinstance(item, (ModuleRouterBase,)):
                _module_routers.append(item)

        return _module_routers


TAppModuleValue = t.Union[ModuleBase, BaseModuleDecorator]
TAppModule = t.Dict[t.Type[ModuleBase], TAppModuleValue]


class ApplicationModuleDecorator(ModuleDecorator):
    __slots__ = (
        "_routes",
        "_module_class",
        "name",
        "_controllers",
        "_services",
        "_template_folder",
        "_static_folder",
        "_module_base_directory",
        "_module_routers",
        "_app_modules",
        "_global_guards",
        "_templating_modules",
    )

    def __init__(
        self,
        *,
        controllers: t.Sequence[t.Union[ControllerDecorator, t.Type]] = tuple(),
        routers: t.Sequence[t.Union[ModuleRouterBase, Mount]] = tuple(),
        services: t.Sequence[t.Union[t.Type, ProviderConfig]] = tuple(),
        modules: t.Sequence[
            t.Union[t.Type, BaseModuleDecorator, ModuleBase, t.Type[ModuleBase]]
        ] = tuple(),
        global_guards: t.List[
            t.Union[t.Type[GuardCanActivate], GuardCanActivate]
        ] = None,
        template_folder: t.Optional[str] = "templates",
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
        self._templating_modules: t.Dict[t.Type[ModuleBase], BaseModuleDecorator] = {}

    @property
    def templating_modules(self) -> t.Dict[t.Type[ModuleBase], BaseModuleDecorator]:
        return self._templating_modules

    @property
    def global_guards(
        self,
    ) -> t.List[t.Union[t.Type[GuardCanActivate], GuardCanActivate]]:
        return self._global_guards

    def validate_module_decorator(self) -> None:
        super().validate_module_decorator()
        self._validate_modules()

    def _validate_modules(self) -> None:
        for module in self._app_modules:
            if not isinstance(module, (BaseModuleDecorator, ModuleBase)):
                raise ImproperConfiguration(
                    f"Object is an invalid Module type. {module}."
                )
            if isinstance(module, ApplicationModuleDecorator):
                raise ImproperConfiguration(
                    f"An app instance is entitled to one ApplicationModule. {module}."
                )

    def configure_module(self, container: Container) -> None:
        self.validate_module_decorator()
        super().configure_module(container=container)

        for module in self._app_modules:
            if isinstance(module, BaseModuleDecorator):
                module.validate_module_decorator()
            container.install(module)

    def build(self) -> ModuleData:
        data: ModuleData = ModuleDecoratorBuilder.default()

        _modules: t.List[
            t.Union[ModuleBase, BaseModuleDecorator, t.Type[ModuleBase], t.Type]
        ] = [self]
        _modules.extend(self._app_modules)

        for module in reversed(_modules):
            ModuleDecoratorBuilder.extend(data, module)
        self._templating_modules = self._get_modules_as_dict(_modules)
        return data

    def get_module_routers(self) -> t.List[ModuleRouterBase]:
        _module_routers = super().get_module_routers()

        for module in self._app_modules:
            if isinstance(module, BaseModuleDecorator):
                _module_routers.extend(module.get_module_routers())

        return _module_routers

    def _get_modules_as_dict(
        self,
        modules: t.List[
            t.Union[ModuleBase, BaseModuleDecorator, t.Type[ModuleBase], t.Type]
        ],
    ) -> t.Dict[t.Type[ModuleBase], BaseModuleDecorator]:
        return {
            item.get_module(): item
            for item in modules
            if isinstance(item, BaseModuleDecorator)
        }

    def build_module(
        self,
        container: Container,
        module: t.Union[t.Type, t.Type[ModuleBase], BaseModuleDecorator],
        **init_kwargs: t.Any,
    ) -> t.Tuple[t.Any, ModuleData]:
        if (
            not isinstance(module, BaseModuleDecorator)
            and type(module) != ModuleBaseMeta
        ):
            raise ImproperConfiguration("Module can not be installed")

        if isinstance(module, ApplicationModuleDecorator):
            raise ImproperConfiguration(
                f"An app instance is entitled to one ApplicationModule. '{module}'."
            )

        if (
            isinstance(module, BaseModuleDecorator)
            and module.get_module() in self.templating_modules
        ):
            return (
                module.get_module()(**init_kwargs),
                ModuleDecoratorBuilder.default(),
            )

        if isinstance(module, BaseModuleDecorator):
            module.validate_module_decorator()
            _module_instance = container.install(module=module, **init_kwargs)
            self._templating_modules.update({module.get_module(): module})
        else:
            _module_instance = container.install(module=module, **init_kwargs)

        return _module_instance, ModuleDecoratorBuilder(_module_instance).build()
