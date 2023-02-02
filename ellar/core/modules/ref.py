import inspect
import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from starlette.routing import BaseRoute, Mount

from ellar.constants import (
    CONTROLLER_WATERMARK,
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_METADATA,
    MODULE_REF_TYPES,
    MODULE_WATERMARK,
    ON_REQUEST_SHUTDOWN_KEY,
    ON_REQUEST_STARTUP_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.controller import ControllerType
from ellar.core.routing import ModuleMount
from ellar.core.routing.router.module import controller_router_factory
from ellar.core.templating import ModuleTemplating
from ellar.di import Container, ProviderConfig, injectable, is_decorated_with_injectable
from ellar.di.providers import ModuleProvider
from ellar.reflect import reflect

from .. import Config
from .base import ModuleBase, ModuleBaseMeta

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import App, ControllerBase


class InvalidModuleTypeException(Exception):
    pass


def create_module_ref_factor(
    module_type: t.Union[t.Type, t.Type[ModuleBase]],
    config: Config,
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
    def config(self) -> Config:
        """gets module ref config"""

    @property
    @abstractmethod
    def module(self) -> t.Union[t.Type[ModuleBase], t.Type]:
        """gets module ref container"""

    @property
    def routes(self) -> t.List[BaseRoute]:
        return []

    def run_module_register_services(self) -> None:
        self.module.before_init(config=self.config)
        _module_type_instance = self.get_module_instance()
        self.container.install(_module_type_instance)  # support for injector module
        # _module_type_instance.register_services(self.container)

    def _build_init_kwargs(self, kwargs: t.Dict) -> t.Dict:
        _result = dict()
        if hasattr(self.module, "__init__"):
            signature = inspect.signature(self.module.__init__)
            for k, v in signature.parameters.items():
                if (
                    v.kind == inspect.Parameter.KEYWORD_ONLY
                    or v.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
                ) and v.default != inspect.Parameter.empty:
                    _result[k] = v.default
        _result.update(kwargs)
        return _result

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
        config: Config,
        **kwargs: t.Any,
    ) -> None:
        assert (
            type(module_type) == ModuleBaseMeta
        ), f"Module Type must be a subclass of ModuleBase;\n Invalid Type[{module_type}]"
        self._module_type: t.Type[ModuleBase] = module_type
        self._init_kwargs = self._build_init_kwargs(kwargs)
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
    def config(self) -> Config:
        return self._config

    def _register_module(self) -> None:
        _module = self.module
        if not is_decorated_with_injectable(self.module):
            _module = injectable()(self.module)
        self.container.register(
            _module, ModuleProvider(self.module, **self._init_kwargs)
        )


class ModuleTemplateRef(ModuleRefBase, ModuleTemplating):
    ref_type: str = MODULE_REF_TYPES.TEMPLATE

    def __init__(
        self,
        module_type: t.Union[t.Type[ModuleBase], t.Type],
        *,
        container: Container,
        config: Config,
        **kwargs: t.Any,
    ) -> None:
        assert (
            type(module_type) == ModuleBaseMeta
        ), f"Module Type must be a subclass of ModuleBase;\n Invalid Type[{module_type}]"

        self._module_type: t.Type[ModuleBase] = module_type
        self._container = container
        self._config = config
        self._init_kwargs = self._build_init_kwargs(kwargs)
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

        self._routers: t.Sequence[
            t.Union[BaseRoute, ModuleMount, Mount]
        ] = self._get_all_routers()
        self._flatten_routes: t.List[BaseRoute] = []

        self.scan_templating_filters()
        self.scan_request_events()
        self.scan_exceptions_handlers()
        self.scan_middle_ware()

    @property
    def module(self) -> t.Type[ModuleBase]:
        return self._module_type

    @property
    def container(self) -> Container:
        return self._container

    @property
    def config(self) -> Config:
        return self._config

    @property
    def routers(self) -> t.Sequence[t.Union[BaseRoute, ModuleMount, Mount]]:
        return self._routers

    @property
    def routes(self) -> t.List[BaseRoute]:
        if not self._flatten_routes:
            for router in self._routers:
                # if isinstance(router, ModuleMount):
                #     # TODO: Allow users to choose whether to run flatten route of group routes together
                #     # router.build_child_routes()
                #     self._flatten_routes.append(router)
                #     continue
                # if isinstance(router, BaseRoute):
                #     self._flatten_routes.append(router)
                if isinstance(router, BaseRoute):
                    self._flatten_routes.append(router)
        return self._flatten_routes

    def run_module_register_services(self) -> None:
        self.register_providers()
        self.register_controllers()
        super(ModuleTemplateRef, self).run_module_register_services()

    def _register_module(self) -> None:
        _module = self.module
        if not is_decorated_with_injectable(self.module):
            _module = injectable()(self.module)
        self.container.register(
            _module, ModuleProvider(self.module, **self._init_kwargs)
        )

    def scan_templating_filters(self) -> None:
        templating_filter = (
            reflect.get_metadata(TEMPLATE_FILTER_KEY, self._module_type) or {}
        )
        if not self._config.get(TEMPLATE_FILTER_KEY) or not isinstance(
            self._config[TEMPLATE_FILTER_KEY], dict
        ):
            self._config[TEMPLATE_FILTER_KEY] = dict()
        self._config[TEMPLATE_FILTER_KEY].update(templating_filter)

        templating_global_filter = (
            reflect.get_metadata(TEMPLATE_GLOBAL_KEY, self._module_type) or {}
        )
        if not self._config.get(TEMPLATE_GLOBAL_KEY) or not isinstance(
            self._config[TEMPLATE_GLOBAL_KEY], dict
        ):
            self._config[TEMPLATE_GLOBAL_KEY] = dict()
        self._config[TEMPLATE_GLOBAL_KEY].update(templating_global_filter)

    def scan_exceptions_handlers(self) -> None:
        exception_handlers = (
            reflect.get_metadata(EXCEPTION_HANDLERS_KEY, self._module_type) or []
        )
        self._config[EXCEPTION_HANDLERS_KEY].extend(exception_handlers)

    def scan_middle_ware(self) -> None:
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

    def run_application_ready(self, app: "App") -> None:
        _module_type_instance = self._container.injector.get(self._module_type)
        _module_type_instance.application_ready(app)

    def _get_all_routers(self) -> t.Sequence[t.Union[ModuleMount, Mount, BaseRoute]]:
        _routers = list(
            reflect.get_metadata(MODULE_METADATA.ROUTERS, self._module_type) or []
        )
        for controller in self._controllers:
            assert reflect.get_metadata(
                CONTROLLER_WATERMARK, controller
            ) and isinstance(controller, ControllerType), "Invalid Controller Type."
            _routers.append(controller_router_factory(controller))
        return _routers

    def scan_request_events(self) -> None:
        request_startup = (
            reflect.get_metadata(ON_REQUEST_STARTUP_KEY, self._module_type) or []
        )
        if not self._config.get(ON_REQUEST_STARTUP_KEY) or not isinstance(
            self._config[ON_REQUEST_STARTUP_KEY], list
        ):
            self._config[ON_REQUEST_STARTUP_KEY] = []
        self._config[ON_REQUEST_STARTUP_KEY].extend(request_startup)

        request_shutdown = (
            reflect.get_metadata(ON_REQUEST_SHUTDOWN_KEY, self._module_type) or []
        )
        if not self._config.get(ON_REQUEST_SHUTDOWN_KEY) or not isinstance(
            self._config[ON_REQUEST_SHUTDOWN_KEY], list
        ):
            self._config[ON_REQUEST_SHUTDOWN_KEY] = []
        self._config[ON_REQUEST_SHUTDOWN_KEY].extend(request_shutdown)
