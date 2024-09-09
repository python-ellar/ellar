import dataclasses
import typing as t
from functools import cached_property

from ellar.common import ControllerBase, ModuleRouter
from ellar.common.constants import MODULE_METADATA, MODULE_WATERMARK
from ellar.common.exceptions import ImproperConfiguration
from ellar.core.conf import Config
from ellar.core.modules.ref.forward import ModuleForwardRef
from ellar.di import (
    MODULE_REF_TYPES,
    Container,
    EllarInjector,
    ModuleTreeManager,
    ProviderConfig,
)
from ellar.reflect import fail_silently, reflect
from ellar.utils.importer import import_from_string
from starlette.routing import BaseRoute

from .base import ModuleBase, ModuleBaseMeta
from .ref import ModuleRefBase, create_module_ref_factor

if t.TYPE_CHECKING:  # pragma: no cover
    import click
    from ellar.common import IModuleSetup


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

    commands: t.Sequence[t.Union["click.Command", "click.Group", t.Any]] = (
        dataclasses.field(default_factory=lambda: ())
    )

    exports: t.List[t.Union[t.Type, t.Any]] = dataclasses.field(
        default_factory=lambda: []
    )

    _is_configured: bool = False

    def __post_init__(self) -> None:
        if not reflect.get_metadata(MODULE_WATERMARK, self.module):
            if not isinstance(self.module, ModuleBaseMeta):
                raise ImproperConfiguration(
                    f"{self.module.__name__} is not a valid Module"
                )

        # # Commands needs to be registered so that
        # if self.commands:
        #     reflect.define_metadata(MODULE_METADATA.COMMANDS, self.commands, self.module)

    def apply_configuration(self) -> None:
        if self._is_configured:
            return

        kwargs = {
            MODULE_METADATA.CONTROLLERS: list(self.controllers),
            MODULE_METADATA.ROUTERS: list(self.routers),
            MODULE_METADATA.PROVIDERS: list(self.providers),
            MODULE_METADATA.COMMANDS: list(self.commands),
            MODULE_METADATA.EXPORTS: list(self.exports),
        }
        for key in kwargs.keys():
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


    def module_a_configuration_factory(module_ref: ModuleRefBase, config: Config, foo: Foo):
        return module_ref.module.setup(param1=config.param1, param2=config.param2, foo=foo.foo)


    @Module(modules=[ModuleSetup(MyModule, inject=[Config, Foo], factory=module_a_configuration_factory), ])
    Class ApplicationModule(ModuleBase):
        pass
    """

    # Module type to be configured
    module: t.Type[t.Union["ModuleBase", "IModuleSetup", t.Any]]

    # `inject` property holds collection types to be injected to `use_factory` method.
    # the order at which the types are defined becomes the order at which they are injected.

    inject: t.Sequence[t.Union[t.Type, t.Any]] = dataclasses.field(
        default_factory=lambda: []
    )

    init_kwargs: t.Dict[t.Any, t.Any] = dataclasses.field(default_factory=lambda: {})
    factory: t.Union[
        t.Callable[["ModuleRefBase"], DynamicModule],
        t.Callable[..., DynamicModule],
        None,
    ] = None

    def __post_init__(self) -> None:
        if not reflect.get_metadata(MODULE_WATERMARK, self.module):
            if not isinstance(self.module, ModuleBaseMeta):
                raise ImproperConfiguration(
                    f"{self.module.__name__} is not a valid Module"
                )

    @cached_property
    def name(self) -> str:
        return t.cast(str, reflect.get_metadata(MODULE_METADATA.NAME, self.module))

    @cached_property
    def ref_type(self) -> str:
        class_names = {cls.__name__ for cls in self.inject}
        if "App" in class_names:
            return MODULE_REF_TYPES.APP_DEPENDENT
        return MODULE_REF_TYPES.DYNAMIC

    @cached_property
    def exports(self) -> t.List[t.Type]:
        return list(reflect.get_metadata(MODULE_METADATA.EXPORTS, self.module) or [])

    @cached_property
    def providers(self) -> t.Dict[t.Type, t.Type]:
        _providers = list(
            reflect.get_metadata(MODULE_METADATA.PROVIDERS, self.module) or []
        )
        res = {}
        for item in _providers:
            if isinstance(item, ProviderConfig):
                res.update({item: item.get_type()})
            else:
                res.update({item: item})
        return res  # type:ignore[return-value]

    @property
    def is_ready(self) -> bool:
        raise Exception(f"{self.module} is not ready")

    def get_module_ref(self, config: "Config", container: Container) -> ModuleRefBase:
        if self.factory is not None:
            ref = self._configure_with_factory(config, container)
        else:
            ref = create_module_ref_factor(
                self.module, config, container, **self.init_kwargs
            )

        assert isinstance(
            ref, ModuleRefBase
        ), f"{ref.module} is not properly configured."

        ref.initiate_module_build()
        return ref

    def _configure_with_factory(
        self, config: "Config", container: Container
    ) -> "ModuleRefBase":
        if self.ref_type == MODULE_REF_TYPES.APP_DEPENDENT:
            app = fail_silently(container.injector.get, interface="App")
            assert app, "Application is not ready"

        services = self._get_services(container.injector)
        init_kwargs = dict(self.init_kwargs)

        ref = create_module_ref_factor(self.module, config, container, **init_kwargs)
        ref.container.injector.tree_manager.add_or_update(
            module_type=self.module, value=ref
        )

        assert self.factory

        res = self.factory(ref, *services)
        if not isinstance(res, DynamicModule):
            raise ImproperConfiguration(
                f"Factory function for {self.module.__name__} module "
                f"configuration must return `DynamicModule` instance"
            )
        res.apply_configuration()

        return ref

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

    def build_and_get_routes(
        self,
        injector: EllarInjector,
        config: "Config",
    ) -> t.List[BaseRoute]:
        ref = self.get_module_ref(config, injector.container)
        ref.build_dependencies()

        return ref.get_routes()

    def __hash__(self) -> int:  # pragma: no cover
        return hash(self.module)


class _ModuleValidateBase:
    def validate_module(self, module: t.Type["ModuleBase"]) -> None:
        if not reflect.get_metadata(MODULE_WATERMARK, module):
            raise ImproperConfiguration(f"{module.__name__} is not a valid Module")


class ForwardRefModule(_ModuleValidateBase):
    __slots__ = ("module",)

    def __init__(
        self,
        module: t.Optional[t.Union[t.Type, str]] = None,
        module_name: t.Optional[str] = None,
    ) -> None:
        self.module = module
        self.module_name = module_name

        if bool(module) == bool(module_name):
            raise ImproperConfiguration(
                "ForwardRefModule can only take one parameter, `module` or `module_name`"
            )

    def resolve_module_dependency(self, parent_module_ref: "ModuleRefBase") -> None:
        tree_manager = parent_module_ref.container.injector.tree_manager
        module_ref = (
            self.get_module_dependency_by_name(tree_manager, parent_module_ref)
            if self.module_name
            else self.get_module_dependency_by_type(tree_manager, parent_module_ref)
        )
        forward_ref = ModuleForwardRef(module_ref)

        tree_manager.add_forward_ref(parent_module_ref.module, forward_ref)

    def get_module_dependency_by_name(
        self, tree_manager: ModuleTreeManager, parent_module_ref: "ModuleRefBase"
    ) -> "ModuleRefBase":
        assert self.module_name, "'module_name' can't be None"

        node = next(
            tree_manager.find_module(lambda data: data.name == self.module_name)
        )

        if node is None:
            raise ImproperConfiguration(
                f"ForwardRefModule module_name='{self.module_name}' "
                f"defined in {parent_module_ref.module} could not be found.\n"
                f"Please kindly ensure a @Module(name={self.module_name}) is registered"
            )

        return t.cast(ModuleRefBase, node.value)

    def get_module_dependency_by_type(
        self, tree_manager: ModuleTreeManager, parent_module_ref: "ModuleRefBase"
    ) -> "ModuleRefBase":
        if isinstance(self.module, str):
            try:
                module_cls: t.Type["ModuleBase"] = t.cast(
                    t.Type["ModuleBase"], import_from_string(self.module)
                )
            except Exception as ex:
                raise ImproperConfiguration(
                    f"Unable to import '{self.module}' registered in '{parent_module_ref.module}'"
                ) from ex
        else:
            module_cls = t.cast(t.Type["ModuleBase"], self.module)

        node = tree_manager.get_module(module_cls)

        if node is None:
            raise ImproperConfiguration(
                f"ForwardRefModule module='{self.module}' "
                f"defined in {parent_module_ref.module} could not be found.\n"
                f"Please kindly ensure a {self.module} is decorated with @Module() is registered"
            )

        return t.cast(ModuleRefBase, node.value)

    def __hash__(self) -> int:  # pragma: no cover
        return hash((self.module, "ForwardRefModule"))


class LazyModuleImport(_ModuleValidateBase):
    __slots__ = ("module", "setup_method", "setup_method_options")

    def __init__(
        self, module: str, setup_method: t.Optional[str] = None, **setup_options: t.Any
    ) -> None:
        self.module = module
        self.setup_method = setup_method
        self.setup_method_options = dict(setup_options)

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
