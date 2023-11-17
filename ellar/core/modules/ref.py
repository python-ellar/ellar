import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from ellar.common.constants import (
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_METADATA,
    MODULE_WATERMARK,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.common.models import ControllerBase
from ellar.common.routing import ModuleMount
from ellar.common.templating import ModuleTemplating
from ellar.common.utils import build_init_kwargs
from ellar.di import (
    MODULE_REF_TYPES,
    Container,
    ProviderConfig,
    injectable,
    is_decorated_with_injectable,
)
from ellar.di.providers import ModuleProvider
from ellar.reflect import reflect
from starlette.routing import BaseRoute, Mount

from ..routing import get_controller_builder_factory
from .base import ModuleBase, ModuleBaseMeta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import Config


class InvalidModuleTypeException(Exception):
    pass


def create_module_ref_factor(
    module_type: t.Union[t.Type, t.Type[ModuleBase]],
    config: "Config",
    container: Container,
    **init_kwargs: t.Any,
) -> t.Union["ModuleRefBase", "ModuleTemplateRef"]:
    module_ref: t.Union["ModuleRefBase", "ModuleTemplateRef"]
    if reflect.get_metadata(MODULE_WATERMARK, module_type):
        module_ref = ModuleTemplateRef(
            module_type,
            container=container,
            config=config,
            **init_kwargs,
        )
        return module_ref
    elif type(module_type) == ModuleBaseMeta:
        module_ref = ModulePlainRef(
            module_type,
            container=container,
            config=config,
            **init_kwargs,
        )
        return module_ref
    raise InvalidModuleTypeException(
        f"{module_type.__name__} must be a subclass of `ellar.core.ModuleBase`"
    )


class ModuleRefBase(ABC):
    ref_type: str = MODULE_REF_TYPES.PLAIN

    @property
    @abstractmethod
    def container(self) -> Container:
        """gets module ref container"""

    @property
    @abstractmethod
    def config(self) -> "Config":
        """gets module ref config"""

    @property
    @abstractmethod
    def module(self) -> t.Union[t.Type[ModuleBase], t.Type]:
        """gets module ref container"""

    @property
    def routes(self) -> t.List[BaseRoute]:
        return []

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
        return self.container.injector.get(self.module)  # type:ignore


class ModulePlainRef(ModuleRefBase):
    ref_type: str = MODULE_REF_TYPES.PLAIN

    def __init__(
        self,
        module_type: t.Union[t.Type[ModuleBase], t.Type],
        *,
        container: Container,
        config: "Config",
        **kwargs: t.Any,
    ) -> None:
        assert (
            type(module_type) == ModuleBaseMeta
        ), f"Module Type must be a subclass of ModuleBase;\n Invalid Type[{module_type}]"
        self._module_type: t.Type[ModuleBase] = module_type
        self._init_kwargs = build_init_kwargs(self.module, kwargs)
        self._container = container
        self._config = config
        self._register_module()

    @property
    def module(self) -> t.Type[ModuleBase]:
        return self._module_type

    @property
    def container(self) -> Container:
        return self._container

    @property
    def config(self) -> "Config":
        return self._config

    def _register_module(self) -> None:
        if not is_decorated_with_injectable(self.module):
            self._module_type = injectable()(self.module)
        self.container.register(
            self._module_type, ModuleProvider(self.module, **self._init_kwargs)
        )


class ModuleTemplateRef(ModuleRefBase, ModuleTemplating):
    ref_type: str = MODULE_REF_TYPES.TEMPLATE

    def __init__(
        self,
        module_type: t.Union[t.Type[ModuleBase], t.Type],
        *,
        container: Container,
        config: "Config",
        **kwargs: t.Any,
    ) -> None:
        self._module_type: t.Type[ModuleBase] = module_type
        self._container = container
        self._config = config
        self._init_kwargs = build_init_kwargs(self.module, kwargs)
        self._register_module()

        self._template_folder: t.Optional[str] = reflect.get_metadata(
            MODULE_METADATA.TEMPLATE_FOLDER, module_type
        )
        self._base_directory: t.Optional[t.Union[Path, str]] = reflect.get_metadata(
            MODULE_METADATA.BASE_DIRECTORY, module_type
        )
        self._static_folder: t.Optional[str] = reflect.get_metadata(
            MODULE_METADATA.STATIC_FOLDER, module_type
        )
        self._controllers: t.List[t.Type[ControllerBase]] = (
            reflect.get_metadata(MODULE_METADATA.CONTROLLERS, self._module_type) or []
        )

        self._routers: t.List[t.Union[BaseRoute]] = self._get_all_routers()
        # self._flatten_routes: t.List[BaseRoute] = []

        if isinstance(self.module, type) and issubclass(self.module, ModuleBase):
            self.scan_templating_filters()
            self.scan_exceptions_handlers()
            self.scan_middleware()

        self.register_providers()
        self.register_controllers()
        # self._build_flatten_routes()

    @property
    def module(self) -> t.Type[ModuleBase]:
        return self._module_type

    @property
    def container(self) -> Container:
        return self._container

    @property
    def config(self) -> "Config":
        return self._config

    @property
    def routers(self) -> t.Sequence[t.Union[BaseRoute, ModuleMount, Mount]]:
        return self._routers

    @property
    def routes(self) -> t.List[BaseRoute]:
        return self._routers

    # def _build_flatten_routes(self) -> None:
    #     for router in self._routers:
    #         # if isinstance(router, ModuleMount):
    #         #     # TODO: Allow users to choose whether to run flatten route of group routes together
    #         #     # router.build_child_routes()
    #         #     self._flatten_routes.append(router)
    #         #     continue
    #         # if isinstance(router, BaseRoute):
    #         #     self._flatten_routes.append(router)
    #         if isinstance(router, BaseRoute):
    #             self._flatten_routes.append(router)

    def _register_module(self) -> None:
        self.container.register(
            self.module, ModuleProvider(self.module, **self._init_kwargs)
        )

    def scan_templating_filters(self) -> None:
        templating_filter = (
            reflect.get_metadata(TEMPLATE_FILTER_KEY, self._module_type) or {}
        )
        if not self._config.get(TEMPLATE_FILTER_KEY) or not isinstance(
            self._config[TEMPLATE_FILTER_KEY], dict
        ):
            self._config[TEMPLATE_FILTER_KEY] = {}
        self._config[TEMPLATE_FILTER_KEY].update(templating_filter)

        templating_global_filter = (
            reflect.get_metadata(TEMPLATE_GLOBAL_KEY, self._module_type) or {}
        )
        if not self._config.get(TEMPLATE_GLOBAL_KEY) or not isinstance(
            self._config[TEMPLATE_GLOBAL_KEY], dict
        ):
            self._config[TEMPLATE_GLOBAL_KEY] = {}
        self._config[TEMPLATE_GLOBAL_KEY].update(templating_global_filter)

    def scan_exceptions_handlers(self) -> None:
        exception_handlers = (
            reflect.get_metadata(EXCEPTION_HANDLERS_KEY, self._module_type) or []
        )
        self._config[EXCEPTION_HANDLERS_KEY].extend(exception_handlers)

    def scan_middleware(self) -> None:
        middleware = (
            reflect.get_metadata(MIDDLEWARE_HANDLERS_KEY, self._module_type) or []
        )
        if not self._config.get(MIDDLEWARE_HANDLERS_KEY) or not isinstance(
            self._config[MIDDLEWARE_HANDLERS_KEY], list
        ):
            self._config[MIDDLEWARE_HANDLERS_KEY] = []
        self._config[MIDDLEWARE_HANDLERS_KEY].extend(middleware)

    def register_providers(self) -> None:
        providers = (
            reflect.get_metadata(MODULE_METADATA.PROVIDERS, self._module_type) or []
        )
        for item in providers:
            provider = item
            if not isinstance(item, ProviderConfig):
                provider = ProviderConfig(item)
            provider.register(self._container)

    def register_controllers(self) -> None:
        for controller in self._controllers:
            ProviderConfig(controller).register(self._container)

    def _get_all_routers(self) -> t.List[BaseRoute]:
        _routers = list(
            reflect.get_metadata(MODULE_METADATA.ROUTERS, self._module_type) or []
        )
        result = []

        for controller in self._controllers + _routers:
            factory_builder = get_controller_builder_factory(type(controller))
            factory_builder.check_type(controller)
            result.append(factory_builder.build(controller))
        return result  # type: ignore[return-value]
