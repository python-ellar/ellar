import typing as t
from pathlib import Path

from injector import AssistedBuilder, singleton
from starlette.routing import BaseRoute

from ellar.constants import (
    CONTROLLER_WATERMARK,
    EXCEPTION_HANDLERS_KEY,
    MIDDLEWARE_HANDLERS_KEY,
    MODULE_METADATA,
    MODULE_REF_TYPES,
    ON_REQUEST_SHUTDOWN_KEY,
    ON_REQUEST_STARTUP_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.controller import ControllerType
from ellar.core.routing import ModuleRouterBase
from ellar.core.routing.router.module import controller_router_factory
from ellar.core.templating import ModuleTemplating
from ellar.di import Container, ProviderConfig
from ellar.reflect import reflect

from .. import Config
from .base import ModuleBase

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import App, ControllerBase


class ModulePlainRef:
    ref_type: str = MODULE_REF_TYPES.PLAIN

    def __init__(
        self,
        module_type: t.Type[ModuleBase],
        *,
        container: Container,
        config: Config,
        **kwargs: t.Any
    ) -> None:
        self._module_type = module_type
        self._init_kwargs = kwargs
        self._container = container
        self._config = config
        self._register_module()
        self.run_module_register_services()

    @property
    def module(self) -> t.Type[ModuleBase]:
        return self._module_type

    def get_module_instance(self) -> ModuleBase:
        builder: AssistedBuilder = self._container.injector.get(
            AssistedBuilder[self._module_type]
        )
        return builder.build(**self._init_kwargs)

    def run_module_register_services(self) -> None:
        self._module_type.before_init(config=self._config)
        _module_type_instance = self.get_module_instance()
        self._container.install(_module_type_instance)  # support for injector module
        _module_type_instance.register_services(self._container)

    def _register_module(self) -> None:
        self._container.register(AssistedBuilder[self._module_type], scope=singleton)


class ModuleTemplateRef(ModulePlainRef, ModuleTemplating):
    ref_type: str = MODULE_REF_TYPES.TEMPLATE

    def __init__(
        self,
        module_type: t.Type[ModuleBase],
        *,
        container: Container,
        config: Config,
        **kwargs: t.Any
    ) -> None:
        self._module_type = module_type
        self._container = container
        self._config = config
        self._init_kwargs = kwargs
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

        self._routers = self._get_routers()
        self._flatten_routes: t.List[BaseRoute] = []

        self.scan_templating_filters()
        self.scan_request_events()
        self.scan_exceptions_handlers()
        self.scan_middle_ware()

    def run_module_register_services(self) -> None:
        self.register_providers()
        self.register_controllers()
        super(ModuleTemplateRef, self).run_module_register_services()

    @property
    def routers(self) -> t.List[ModuleRouterBase]:
        return self._routers

    @property
    def routes(self) -> t.List[BaseRoute]:
        if not self._flatten_routes:
            for router in self._routers:
                self._flatten_routes.extend(router.build_routes())
        return self._flatten_routes

    def scan_templating_filters(self) -> None:
        templating_filter = (
            reflect.get_metadata(TEMPLATE_FILTER_KEY, self._module_type) or {}
        )
        self.jinja_environment.filters.update(templating_filter)

        templating_global_filter = (
            reflect.get_metadata(TEMPLATE_GLOBAL_KEY, self._module_type) or {}
        )
        self.jinja_environment.globals.update(templating_global_filter)

    def scan_exceptions_handlers(self) -> None:
        exception_handlers = (
            reflect.get_metadata(EXCEPTION_HANDLERS_KEY, self._module_type) or {}
        )
        self._config[EXCEPTION_HANDLERS_KEY].update(exception_handlers)

    def scan_middle_ware(self) -> None:
        middleware = (
            reflect.get_metadata(MIDDLEWARE_HANDLERS_KEY, self._module_type) or []
        )
        if not self._config[MIDDLEWARE_HANDLERS_KEY] or not isinstance(
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

    def register_controllers(self):
        for controller in self._controllers:
            ProviderConfig(controller).register(self._container)

    def run_application_ready(self, app: "App") -> None:
        _module_type_instance = self._container.injector.get(self._module_type)
        _module_type_instance.application_ready(app)

    def _get_routers(self) -> t.List[ModuleRouterBase]:
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
        if not self._config[ON_REQUEST_STARTUP_KEY] or not isinstance(
            self._config[ON_REQUEST_STARTUP_KEY], list
        ):
            self._config[ON_REQUEST_STARTUP_KEY] = []
        self._config[ON_REQUEST_STARTUP_KEY].extend(request_startup)

        request_shutdown = (
            reflect.get_metadata(ON_REQUEST_SHUTDOWN_KEY, self._module_type) or []
        )
        if not self._config[ON_REQUEST_SHUTDOWN_KEY] or not isinstance(
            self._config[ON_REQUEST_SHUTDOWN_KEY], list
        ):
            self._config[ON_REQUEST_SHUTDOWN_KEY] = []
        self._config[ON_REQUEST_SHUTDOWN_KEY].extend(request_shutdown)
