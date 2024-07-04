import typing as t
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from ellar.auth.constants import POLICY_KEYS
from ellar.auth.policy.base import _PolicyHandlerWithRequirement
from ellar.common import ControllerBase, ModuleRouter
from ellar.common.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
    GUARDS_KEY,
    MODULE_METADATA,
    MODULE_WATERMARK,
    ROUTE_INTERCEPTORS,
)
from ellar.core.conf import Config
from ellar.core.context import ApplicationContext
from ellar.core.modules.base import ModuleBase
from ellar.core.router_builders import get_controller_builder_factory
from ellar.core.routing import EllarMount, RouteOperation, RouteOperationBase
from ellar.di import (
    MODULE_REF_TYPES,
    Container,
    ProviderConfig,
    is_decorated_with_injectable,
)
from ellar.reflect import reflect
from injector import Scope, ScopeDecorator
from starlette.routing import BaseRoute
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
        self._providers: t.Dict[t.Type, t.Type] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} module={self.module}>"

    @property
    def is_ready(self) -> bool:
        return True

    @property
    def exports(self) -> t.List[t.Type]:
        """gets module ref config"""
        return self._exports

    @property
    def providers(self) -> t.Dict[t.Type, t.Type]:
        """gets module ref config"""
        return self._providers.copy()

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
        self._build_module_parameters()

        self.container.injector.tree_manager.add_or_update(
            module_type=self.module, value=self
        )

    def run_module_register_services(self) -> None:
        """
        Defer module instantiation till lifespan call
        """
        if hasattr(self.module, "before_init"):
            self.module.before_init(config=self.config)
        _module_type_instance = self.get_module_instance()
        self.container.install(_module_type_instance)  # support for injector module
        # _module_type_instance.register_services(self.container)

    @abstractmethod
    def _register_module(self) -> None:
        """Register Module"""

    def get_module_instance(self) -> ModuleBase:
        root_module = self.container.injector.tree_manager.get_root_module()
        return root_module.container.injector.get(self.module)  # type:ignore

    def export_all(self) -> None:
        self._exports = list(set(self._exports + list(self._providers.keys())))

    @t.no_type_check
    def build_dependencies(self, step: int = -1) -> None:
        modules = list(
            self.container.injector.tree_manager.get_module_dependencies(self.module)
        )
        for idx, module_config in enumerate(reversed(modules)):
            if step != -1 and idx + 1 > step:
                break

            ref = module_config.value
            if not isinstance(module_config.value, ModuleRefBase):
                ref = module_config.value.get_module_ref(self.config, self.container)

            ref.build_dependencies(step - 1 if step != -1 else step)

    def get_routes(self) -> t.List[BaseRoute]:
        routes = [] + self.routes
        modules = list(
            self.container.injector.tree_manager.get_module_dependencies(self.module)
        )
        for module_config in reversed(modules):
            routes.extend(module_config.value.get_routes())

        return routes

    @asynccontextmanager
    async def context(self) -> t.AsyncGenerator[ApplicationContext, None]:
        async with ApplicationContext(self.container.injector) as context:
            yield context

    def add_exports(self, provider_type: t.Type) -> None:
        # validate export
        def _validate_() -> None:
            if provider_type not in self._providers:
                module = next(
                    self.container.injector.tree_manager.find_module(
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
            self.config.OVERRIDE_CORE_SERVICE.insert(0, provider)
        else:
            self._providers.update({provider_type: provider_type})
            provider.register(self.container)

            if provider.export or export:
                self.add_exports(provider_type)

    def _build_module_parameters(self) -> None:
        from ellar.core.modules.config import ForwardRefModule

        if reflect.get_metadata(MODULE_WATERMARK, self.module):
            _routers: t.List[t.Any] = list(
                reflect.get_metadata(MODULE_METADATA.ROUTERS, self.module) or []
            )
            _controllers: t.List[t.Type[ControllerBase]] = (
                reflect.get_metadata(MODULE_METADATA.CONTROLLERS, self.module) or []
            )
            _providers = list(
                reflect.get_metadata(MODULE_METADATA.PROVIDERS, self.module) or []
            )

            _exports = list(
                reflect.get_metadata(MODULE_METADATA.EXPORTS, self.module) or []
            )

            modules = reflect.get_metadata(MODULE_METADATA.MODULES, self.module) or []

            self._search_providers_in_controller(_controllers)
            self._search_providers_in_controller(_routers)

            for provider in _providers:
                self.add_provider(provider)

            for export in _exports:
                self.add_exports(export)

            for module in modules:
                if isinstance(module, ForwardRefModule):
                    module.resolve_module_dependency(self)

    def _search_providers_in_controller(
        self, controllers: t.List[t.Union[t.Type, t.Any]]
    ) -> None:
        for controller in controllers:
            factory_builder = get_controller_builder_factory(type(controller))
            factory_builder.check_type(controller)

            self._routers.append(factory_builder.build(controller))

            control_type = controller
            if isinstance(controller, ModuleRouter):
                control_type = controller.control_type
            elif isinstance(controller, EllarMount):
                control_type = controller.get_control_type()
            elif not isinstance(controller, type):
                continue

            self._search_controller_routes_injectables(control_type)
            self._run_all_checks(control_type)

    def _search_controller_routes_injectables(self, control_type: t.Type) -> None:
        operations: t.List[RouteOperation] = (
            reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, control_type) or []
        )
        for operation in operations:
            if isinstance(operation, RouteOperationBase):
                self._run_all_checks(operation.endpoint)
            elif isinstance(operation, EllarMount):
                self._search_controller_routes_injectables(operation.get_control_type())
                self._run_all_checks(operation.get_control_type())

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
