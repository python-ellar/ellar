import dataclasses
import typing as t
from abc import abstractmethod

from starlette.routing import BaseRoute

import ellar.core.conf as conf
import ellar.core.main as main
import ellar.di as di
from ellar.constants import MODULE_METADATA, MODULE_REF_TYPES
from ellar.reflect import reflect

from .base import ModuleBase
from .ref import ModuleRefBase, create_module_ref_factor

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import ControllerBase


@dataclasses.dataclass
class DynamicModule:
    # Module type to be configured
    module: t.Type[t.Union["ModuleBase", t.Any]]

    providers: t.List[t.Union[t.Type, t.Any]] = dataclasses.field(
        default_factory=lambda: []
    )

    controllers: t.Sequence[
        t.Union[t.Type["ControllerBase"], t.Type]
    ] = dataclasses.field(default_factory=lambda: tuple())
    routers: t.Sequence[t.Union[BaseRoute]] = dataclasses.field(
        default_factory=lambda: tuple()
    )

    def __post_init__(self) -> None:
        if not isinstance(self.module, type) or not issubclass(self.module, ModuleBase):
            raise Exception(f"{self.module.__name__} is not a valid Module")

        kwargs = dict(
            controllers=list(self.controllers),
            routers=list(self.routers),
            providers=list(self.providers),
        )
        for key in [
            MODULE_METADATA.CONTROLLERS,
            MODULE_METADATA.ROUTERS,
            MODULE_METADATA.PROVIDERS,
        ]:
            value = kwargs[key]
            if value:
                reflect.delete_metadata(key, self.module)
                reflect.define_metadata(key, value, self.module)


@dataclasses.dataclass
class ModuleSetup:
    """
    ModuleConfigure is a way to configure a module late after the application has started.
    This is necessary for Module that requires some services available to configure them.
    For example:

    @Module()
    Class ModuleA(ModuleBase):
        def module_configure(cls, setting1: t.Any, setting2: t.Any, setting3: t.Any):
            return ModuleConfigure(module=cls, provider=[])

    def module_a_configuration_factory(module: ModuleA, config: Config, foo: Foo):
            return module.module_configure(setting1=config.setting1, setting2=config.setting2, setting3=foo.foo)


    @Module(modules=[ModuleAConfigure(ModuleA, inject=[Config, Foo], factory=module_a_configuration_factory), ])
    Class ApplicationModule(ModuleBase):
        pass
    """

    # Module type to be configured
    module: t.Type[t.Union[ModuleBase, "IModuleSetup", t.Any]]

    # `inject` property holds collection types to be injected to `use_factory` method.
    # the order at which the types are defined becomes the order at which they are injected.

    ref_type: str = MODULE_REF_TYPES.DYNAMIC

    inject: t.Sequence[t.Union[t.Type, t.Any]] = dataclasses.field(
        default_factory=lambda: []
    )

    init_kwargs: t.Dict[t.Any, t.Any] = dataclasses.field(default_factory=lambda: {})
    factory: t.Callable[..., DynamicModule] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if not isinstance(self.module, type) or not issubclass(self.module, ModuleBase):
            raise Exception(f"{self.module.__name__} is not a valid Module")

        if main.App in self.inject:
            self.ref_type = MODULE_REF_TYPES.APP_DEPENDENT

    @property
    def has_factory_function(self) -> bool:
        if self.factory:
            # if we have a factory function, we need to check if the services to inject is just config
            # if so, then we can go ahead and have the configuration executed since at this level,
            # the config service is available to be injected.
            inject_size = len(self.inject)
            if inject_size == 0:
                return False

            if inject_size == 1 and self.inject[0] == conf.Config:
                return False
            return True

    def get_module_ref(
        self, config: conf.Config, container: di.Container
    ) -> t.Union[ModuleRefBase, "ModuleSetup"]:
        if self.has_factory_function or self.ref_type == MODULE_REF_TYPES.APP_DEPENDENT:
            return self

        if self.factory:
            return self.configure_with_factory(config, container)

        return create_module_ref_factor(
            self.module, config, container, **self.init_kwargs
        )

    def configure_with_factory(
        self, config: conf.Config, container: di.Container
    ) -> ModuleRefBase:
        services = self._get_services(container.injector)

        res = self.factory(self.module, *services)
        if not isinstance(res, DynamicModule):
            raise Exception(
                f"Factory function for {self.module.__name__} module "
                f"configuration must return `DynamicModule` instance"
            )

        init_kwargs = dict(self.init_kwargs)
        return create_module_ref_factor(self.module, config, container, **init_kwargs)

    def _get_services(self, injector: di.EllarInjector) -> t.List:
        """
        Get list of services to be injected to the factory function.
        :param injector:
        :return:
        """
        res = []
        for service in self.inject:
            res.append(injector.get(service))
        return res

    def __hash__(self) -> int:  # pragma: no cover
        return hash(self.module)


class IModuleSetup:
    """Modules that must have a custom setup should inherit from IModuleConfigure"""

    @classmethod
    @abstractmethod
    @t.no_type_check
    def setup(cls, *args: t.Any, **kwargs: t.Any) -> DynamicModule:
        """Module Dynamic Setup"""
