import typing as t
from abc import ABC, abstractmethod
from functools import cached_property
from typing import Type

from ellar.auth.constants import POLICY_KEYS
from ellar.auth.policy.base import _PolicyHandlerWithRequirement
from ellar.common import ControllerBase
from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    GUARDS_KEY,
    MODULE_COMPONENT,
    MODULE_METADATA,
    MODULE_WATERMARK,
    ROUTE_INTERCEPTORS,
)
from ellar.core.conf import Config
from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
from ellar.core.modules.ref.context import ModuleExecutionContext
from ellar.core.modules.ref.forward import ModuleForwardRef
from ellar.core.router_builders import get_controller_builder_factory
from ellar.core.routing import EllarControllerMount, RouteOperationBase
from ellar.di import (
    MODULE_REF_TYPES,
    Container,
    ModuleTreeManager,
    ProviderConfig,
    is_decorated_with_injectable,
)
from ellar.reflect import reflect
from injector import Scope, ScopeDecorator
from starlette.routing import (
    BaseRoute,
    Host,
    Mount,
    WebSocketRoute,
)
from starlette.routing import (
    Route as StarletteRoute,
)
from starlette.routing import (
    Router as StarletteRouter,
)
from typing_extensions import Annotated

_T = t.TypeVar("_T", bound=t.Type)


class ModuleRefBase(ABC):
    ref_type: str = MODULE_REF_TYPES.PLAIN

    def __init__(
        self,
        module_type: t.Union[t.Type[ModuleBase], t.Type],
        container: Container,
        name: str,
        config: "Config",
    ) -> None:
        self._container = container
        self._module = module_type
        self._name = name
        self._config = config

        self._validate_module_type()

        self._routers: t.List[t.Union[BaseRoute]] = []
        self._exports: t.List[t.Type] = []
        self._providers: t.Dict[t.Type, ProviderConfig] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} module={self.module}>"

    def __hash__(self) -> int:
        return hash(self.module)

    @cached_property
    def module_context(self) -> ModuleExecutionContext:
        return ModuleExecutionContext(container=self.container, module=self.module)

    @property
    def tree_manager(self) -> ModuleTreeManager:
        return self.container.injector.tree_manager

    @property
    def is_ready(self) -> bool:
        return True

    @property
    def exports(self) -> t.List[t.Type]:
        """gets module ref config"""
        return self._exports.copy()

    @property
    def providers(self) -> t.Dict[t.Type, ProviderConfig]:
        """gets module ref config"""
        return self._providers.copy()

    @property
    def modules(self) -> t.List[Type["ModuleBase"]]:
        """gets module ref config"""
        return [
            i.value.module  # type:ignore[misc]
            for i in self.tree_manager.get_module_dependencies(self.module)
        ]

    @t.no_type_check
    def get(
        self,
        interface: t.Union[Annotated[t.Type[_T], type], Annotated[str, type], t.Any],
        scope: t.Union[ScopeDecorator, t.Type[Scope]] = None,
    ) -> _T:
        return self.container.injector.get(interface, scope=scope)

    @property
    def container(self) -> Container:
        """gets module ref container"""
        return self._container

    @property
    def name(self) -> str:
        """gets module ref container"""
        return self._name

    @property
    def config(self) -> "Config":
        """gets module ref config"""
        return self._config

    @property
    def module(self) -> t.Union[t.Type[ModuleBase], t.Type]:
        """gets module ref container"""
        return self._module

    @property
    def routes(self) -> t.List[BaseRoute]:
        return self._routers

    @abstractmethod
    def _validate_module_type(self) -> None:
        """Validate Module Type"""

    def initiate_module_build(self) -> None:
        self._register_module()
        self._build_module_parameters_and_routes()

        self.tree_manager.add_or_update(
            module_type=self.module,
            value=self,
            parent_module=(
                self.container.parent.injector.owner.module  # type:ignore[attr-defined]
                if self.container.parent and self.container.parent.injector.owner  # type:ignore[attr-defined]
                else None
            ),
        )

        if isinstance(self.module, ModuleBaseMeta):
            self.module.post_build(self)

    def run_module_register_services(self) -> None:
        """
        Defer module instantiation till lifespan/modules ready call
        """
        from ellar.core.modules.config import ForwardRefModule

        _module_type_instance = self.get_module_instance()
        self.container.install(_module_type_instance)  # support for injector module
        # _module_type_instance.register_services(self.container)
        modules = list(self.tree_manager.get_module_dependencies(self.module))

        for module_config in reversed(modules):
            if isinstance(module_config.value, ModuleForwardRef):
                continue
            module_config.value.run_module_register_services()

        registered_modules = (
            reflect.get_metadata(MODULE_METADATA.MODULES, self.module) or []
        )

        for module in registered_modules:
            if isinstance(module, ForwardRefModule):
                module.resolve_module_dependency(self)

    @abstractmethod
    def _register_module(self) -> None:
        """Register Module"""

    def get_module_instance(self) -> ModuleBase:
        root_module = self.tree_manager.get_app_module()
        return root_module.container.injector.get(self.module)  # type:ignore

    def export_all(self) -> None:
        self._exports = list(set(self._exports + list(self._providers.keys())))

    @t.no_type_check
    def build_dependencies(self, step: int = -1) -> None:
        modules = list(self.tree_manager.get_module_dependencies(self.module))
        for idx, module_config in enumerate(reversed(modules)):
            if step != -1 and idx + 1 > step:
                break

            ref = module_config.value
            if not isinstance(module_config.value, ModuleRefBase):
                ref = module_config.value.get_module_ref(self.config, self.container)

            ref.build_dependencies(step - 1 if step != -1 else step)

    def get_routes(self) -> t.List[BaseRoute]:
        routes = [] + self.routes
        modules = list(self.tree_manager.get_module_dependencies(self.module))
        for module_config in reversed(modules):
            routes.extend(module_config.value.get_routes())

        return routes

    def add_exports(self, provider_type: t.Type) -> None:
        # validate export
        def _validate_() -> None:
            if provider_type not in self._providers:
                module = next(
                    self.tree_manager.find_module(
                        lambda data: provider_type in data.exports
                        and data.parent == self.module
                    )
                )
                assert (
                    module
                ), f"Unknown Export '{provider_type}' found in '{self.module}'"

        _validate_()

        if provider_type not in self.exports:
            self._exports.append(provider_type)

    def add_provider(
        self, provider: t.Union[t.Type, ProviderConfig, t.Any], export: bool = False
    ) -> None:
        if not isinstance(provider, ProviderConfig):
            provider = ProviderConfig(provider, export=export)

        provider_type = provider.get_type()

        if provider.core and provider not in self.config.OVERRIDE_CORE_SERVICE:
            # this will ensure config.py OVERRIDE_CORE_SERVICE takes higher priority
            self.config.OVERRIDE_CORE_SERVICE = [
                provider
            ] + self.config.OVERRIDE_CORE_SERVICE
        else:
            self._providers.update({provider_type: provider})
            provider.register(self.container)

            if provider.export or export:
                self.add_exports(provider_type)

    def build_controllers_and_routers(self) -> None:
        self._routers = []

        _routers: t.List[t.Any] = list(
            reflect.get_metadata(MODULE_METADATA.ROUTERS, self.module) or []
        )
        _controllers: t.List[t.Type[ControllerBase]] = (
            reflect.get_metadata(MODULE_METADATA.CONTROLLERS, self.module) or []
        )
        self._search_providers_and_build_controller(_controllers)
        self._search_providers_and_build_controller(_routers)

    def _build_module_parameters_and_routes(self) -> None:
        if reflect.get_metadata(MODULE_WATERMARK, self.module):
            _providers = list(
                reflect.get_metadata(MODULE_METADATA.PROVIDERS, self.module) or []
            )

            _exports = list(
                reflect.get_metadata(MODULE_METADATA.EXPORTS, self.module) or []
            )

            self.build_controllers_and_routers()

            for provider in _providers:
                self.add_provider(provider)

            for export in _exports:
                self.add_exports(export)

    def _search_providers_and_build_controller(
        self, controllers: t.List[t.Union[t.Type, t.Any]]
    ) -> None:
        for controller in controllers:
            factory_builder = get_controller_builder_factory(type(controller))
            factory_builder.check_type(controller)

            routes_or_mount = factory_builder.build(controller)
            self._run_all_checks(controller)

            for item in (
                routes_or_mount
                if isinstance(routes_or_mount, list)
                else [routes_or_mount]
            ):
                if not isinstance(item, BaseRoute):
                    raise RuntimeError(
                        f"Invalid type registered as a route or router - {item}"
                    )
                self._routers.append(item)

            self._search_controller_routes_injectables(self._routers)

    def _search_controller_routes_injectables(
        self, routes: t.List[BaseRoute], grouped: bool = False
    ) -> None:
        for operation in routes:
            if isinstance(
                operation, (StarletteRoute, RouteOperationBase, WebSocketRoute)
            ):
                self._run_all_checks(operation.endpoint)
            elif isinstance(
                operation, (StarletteRouter, Host, Mount, EllarControllerMount)
            ):
                self._search_controller_routes_injectables(
                    operation.routes, grouped=True
                )
                self._run_all_checks(
                    reflect.get_metadata(CONTROLLER_CLASS_KEY, operation) or ()
                )

            if not grouped:
                reflect.define_metadata(MODULE_COMPONENT, self, operation)

    def _run_all_checks(self, item: t.Union[t.Type, t.Any]) -> None:
        self._search_injectables(item)
        self._search_guards(item)
        self._search_interceptors(item)
        self._search_policies(item)

    def _search_injectables(self, item: t.Union[t.Type, t.Any]) -> None:
        if is_decorated_with_injectable(item):
            self.add_provider(item)

    def _search_guards(self, item: t.Union[t.Type, t.Any]) -> None:
        guards = reflect.get_metadata(GUARDS_KEY, item) or []
        for guard in guards:
            if isinstance(guard, type) and is_decorated_with_injectable(guard):
                self.add_provider(guard)

    def _search_interceptors(self, item: t.Union[t.Type, t.Any]) -> None:
        interceptors = reflect.get_metadata(ROUTE_INTERCEPTORS, item) or []
        for interceptor in interceptors:
            if isinstance(interceptor, type) and is_decorated_with_injectable(
                interceptor
            ):
                self.add_provider(interceptor)

    def _search_policies(self, item: t.Union[t.Type, t.Any]) -> None:
        policies = reflect.get_metadata(POLICY_KEYS, item) or []
        for policy in policies:
            if isinstance(policy, type) and is_decorated_with_injectable(policy):
                self.add_provider(policy)
            elif isinstance(
                policy, _PolicyHandlerWithRequirement
            ) and is_decorated_with_injectable(policy.policy_type):  # type:ignore[type-var]
                self.add_provider(policy.policy_type)
