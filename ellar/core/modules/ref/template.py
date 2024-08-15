import typing as t
from pathlib import Path

from ellar.common.constants import (
    APP_EXCEPTION_HANDLERS_KEY,
    APP_MIDDLEWARE_HANDLERS_KEY,
    MODULE_METADATA,
    MODULE_WATERMARK,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.common.templating import ModuleTemplating
from ellar.core.modules.base import ModuleBase
from ellar.di import (
    MODULE_REF_TYPES,
    Container,
    EllarInjector,
    ProviderConfig,
)
from ellar.di.providers import ModuleProvider
from ellar.reflect import reflect
from ellar.utils import build_init_kwargs, get_name

from .base import ModuleRefBase

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import Config


class ModuleTemplateRef(ModuleRefBase, ModuleTemplating):
    ref_type: str = MODULE_REF_TYPES.TEMPLATE

    def __init__(
        self,
        module_type: t.Union[t.Type[ModuleBase], t.Type],
        *,
        parent_container: t.Optional[Container] = None,
        config: "Config",
        **kwargs: t.Any,
    ) -> None:
        self._init_kwargs = build_init_kwargs(module_type, kwargs)

        self._template_folder: t.Optional[str] = reflect.get_metadata(
            MODULE_METADATA.TEMPLATE_FOLDER, module_type
        )
        self._base_directory: t.Optional[t.Union[Path, str]] = reflect.get_metadata(
            MODULE_METADATA.BASE_DIRECTORY, module_type
        )
        self._static_folder: t.Optional[str] = reflect.get_metadata(
            MODULE_METADATA.STATIC_FOLDER, module_type
        )

        name = reflect.get_metadata(MODULE_METADATA.NAME, module_type) or get_name(
            module_type
        )
        container = EllarInjector(
            auto_bind=config.INJECTOR_AUTO_BIND,
            parent=parent_container.injector if parent_container else None,
            owner=self,
        ).container

        super().__init__(
            module_type=module_type,
            container=container,
            name=name,
            config=config,
        )

    def initiate_module_build(self) -> None:
        super().initiate_module_build()

        if isinstance(self.module, type) and issubclass(self.module, ModuleBase):
            self.scan_templating_filters()
            self.scan_exceptions_handlers()

            self.scan_middleware()

    def _validate_module_type(self) -> None:
        res = reflect.get_metadata(MODULE_WATERMARK, self.module)
        assert (
            res is True
        ), f"Module Type must be decorated with @Module decorator;\n Invalid Module type[{self.module}]"

    def _register_module(self) -> None:
        self.add_provider(
            ProviderConfig(
                self.module,
                use_value=ModuleProvider(self.module, **self._init_kwargs),
                tag=self.name,
            ),
            export=True,
        )

    def scan_templating_filters(self) -> None:
        templating_filter = reflect.get_metadata(TEMPLATE_FILTER_KEY, self.module) or {}
        if templating_filter:
            self.config.TEMPLATE_FILTERS = {
                **self.config.TEMPLATE_FILTERS,
                **templating_filter,
            }

        templating_global_filter = (
            reflect.get_metadata(TEMPLATE_GLOBAL_KEY, self.module) or {}
        )
        if templating_global_filter:
            self.config.TEMPLATE_GLOBAL_FILTERS = {
                **self.config.TEMPLATE_GLOBAL_FILTERS,
                **templating_global_filter,
            }

    def scan_exceptions_handlers(self) -> None:
        app_exceptions = list(
            reflect.get_metadata(APP_EXCEPTION_HANDLERS_KEY, self.module) or []
        )

        if app_exceptions:
            self.config.EXCEPTION_HANDLERS = (
                list(self.config.EXCEPTION_HANDLERS) + app_exceptions
            )

    def scan_middleware(self) -> None:
        app_middleware = list(
            reflect.get_metadata(APP_MIDDLEWARE_HANDLERS_KEY, self.module) or []
        )

        if app_middleware:
            self.config.MIDDLEWARE = list(self.config.MIDDLEWARE) + app_middleware
