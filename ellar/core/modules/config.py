import dataclasses
import typing as t

from ellar.common import ControllerBase, ModuleRouter
from ellar.common.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.common.exceptions import ImproperConfiguration
from ellar.core.conf import Config
from ellar.di import MODULE_REF_TYPES, Container, EllarInjector
from ellar.reflect import reflect
from ellar.utils.importer import import_from_string
from starlette.routing import BaseRoute

from .ref import ModuleRefBase, create_module_ref_factor

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.common import IModuleSetup

    from .base import ModuleBase


@dataclasses.dataclass
class DynamicModule:
    # Module type to be configured
    module: t.Type[t.Union["ModuleBase", t.Any]]

    providers: t.List[t.Union[t.Type, t.Any]] = dataclasses.field(
        default_factory=lambda: []
    )

    controllers: t.Sequence[t.Union[t.Type["ControllerBase"], t.Type]] = (
        dataclasses.field(default_factory=lambda: ())
    )

    routers: t.Sequence[t.Union[BaseRoute, ModuleRouter]] = dataclasses.field(
        default_factory=lambda: ()
    )
    _is_configured: bool = False

    def __post_init__(self) -> None:
        if not reflect.get_metadata(MODULE_WATERMARK, self.module):
            raise ImproperConfiguration(f"{self.module.__name__} is not a valid Module")

    def apply_configuration(self) -> None:
        if self._is_configured:
            return

        kwargs = {
            "controllers": list(self.controllers),
            "routers": list(self.routers),
            "providers": list(self.providers),
        }
        for key in [
            MODULE_METADATA.CONTROLLERS,
            MODULE_METADATA.ROUTERS,
            MODULE_METADATA.PROVIDERS,
        ]:
            value = kwargs[key]
            if value:
                reflect.delete_metadata(key, self.module)
                reflect.define_metadata(key, value, self.module)

        self._is_configured = True


@dataclasses.dataclass
class ModuleSetup:
    """
    ModuleSetup is a way to configure a module based on its dependencies.
    This is necessary for Module that requires some services available to configure them.
    For example:

     @Module()
     class MyModule(ModuleBase, IModuleSetup):
        @classmethod
        def setup(cls, param1: Any, param2: Any, foo: str) -> DynamicModule:
            return DynamicModule(cls, providers=[], controllers=[], routers=[])


    def module_a_configuration_factory(module: Type[MyModule], config: Config, foo: Foo):
        return module.setup(param1=config.param1, param2=config.param2, foo=foo.foo)


    @Module(modules=[ModuleSetup(MyModule, inject=[Config, Foo], factory=module_a_configuration_factory), ])
    Class ApplicationModule(ModuleBase):
        pass
    """

    # Module type to be configured
    module: t.Type[t.Union["ModuleBase", "IModuleSetup", t.Any]]

    # `inject` property holds collection types to be injected to `use_factory` method.
    # the order at which the types are defined becomes the order at which they are injected.

    ref_type: str = MODULE_REF_TYPES.DYNAMIC

    inject: t.Sequence[t.Union[t.Type, t.Any]] = dataclasses.field(
        default_factory=lambda: []
    )

    init_kwargs: t.Dict[t.Any, t.Any] = dataclasses.field(default_factory=lambda: {})
    factory: t.Callable[..., DynamicModule] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if not reflect.get_metadata(MODULE_WATERMARK, self.module):
            raise ImproperConfiguration(f"{self.module.__name__} is not a valid Module")

        class_names = {cls.__name__ for cls in self.inject}
        if "App" in class_names:
            self.ref_type = MODULE_REF_TYPES.APP_DEPENDENT

    @property
    def has_factory_function(self) -> bool:
        if self.factory is not None:
            # if we have a factory function, we need to check if the services to inject is just config
            # if so, then we can go ahead and have the configuration executed since at this level,
            # the config service is available to be injected.
            inject_size = len(self.inject)
            if inject_size == 0:
                return False

            if inject_size == 1 and self.inject[0] == Config:
                return False
            return True

    def get_module_ref(
        self, config: "Config", container: Container
    ) -> t.Union[ModuleRefBase, "ModuleSetup"]:
        if self.has_factory_function or self.ref_type == MODULE_REF_TYPES.APP_DEPENDENT:
            return self

        if self.factory is not None:
            return self.configure_with_factory(config, container)

        return create_module_ref_factor(
            self.module, config, container, **self.init_kwargs
        )

    def configure_with_factory(
        self, config: "Config", container: Container
    ) -> ModuleRefBase:
        services = self._get_services(container.injector)

        res = self.factory(self.module, *services)
        if not isinstance(res, DynamicModule):
            raise ImproperConfiguration(
                f"Factory function for {self.module.__name__} module "
                f"configuration must return `DynamicModule` instance"
            )
        res.apply_configuration()

        init_kwargs = dict(self.init_kwargs)
        return create_module_ref_factor(self.module, config, container, **init_kwargs)

    def _get_services(self, injector: EllarInjector) -> t.List:
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


class LazyModuleImport:
    __slots__ = ("module", "setup_method", "setup_method_options")

    def __init__(
        self, module: str, setup_method: t.Optional[str] = None, **setup_options: t.Any
    ) -> None:
        self.module = module
        self.setup_method = setup_method
        self.setup_method_options = dict(setup_options)

    @classmethod
    def validate_module(cls, module: t.Type["ModuleBase"]) -> None:
        if not reflect.get_metadata(MODULE_WATERMARK, module):
            raise ImproperConfiguration(f"{module.__name__} is not a valid Module")

    def get_module(
        self, root_module_name: t.Optional[str] = None
    ) -> t.Union[t.Type["ModuleBase"], ModuleSetup, DynamicModule]:
        try:
            root_module_name = root_module_name or "ApplicationModule"
            module_cls: t.Type["ModuleBase"] = t.cast(
                t.Type["ModuleBase"], import_from_string(self.module)
            )
        except Exception as ex:
            raise ImproperConfiguration(
                f'Unable to import "{self.module}" registered in "{root_module_name}"'
            ) from ex
        self.validate_module(module_cls)

        if self.setup_method:
            setup_method = getattr(module_cls, self.setup_method)
            module_setup = setup_method(**self.setup_method_options)
            if not isinstance(module_setup, (DynamicModule, ModuleSetup)):
                raise ImproperConfiguration(
                    "Lazy Module import with setup attribute must return a "
                    "DynamicModule/ModuleSetup instance"
                )
            return module_setup

        return module_cls

    def __hash__(self) -> int:  # pragma: no cover
        return hash((self.module, self.setup_method, self.setup_method_options))
