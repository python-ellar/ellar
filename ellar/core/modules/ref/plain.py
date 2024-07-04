import typing as t

from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
from ellar.di import (
    MODULE_REF_TYPES,
    Container,
    ProviderConfig,
    injectable,
    is_decorated_with_injectable,
)
from ellar.di.providers import ModuleProvider
from ellar.utils import build_init_kwargs, get_name

from .base import ModuleRefBase

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import Config


class ModulePlainRef(ModuleRefBase):
    ref_type: str = MODULE_REF_TYPES.PLAIN

    def __init__(
        self,
        module_type: t.Union[t.Type[ModuleBase], t.Type],
        *,
        parent_container: Container,
        config: "Config",
        **kwargs: t.Any,
    ) -> None:
        super().__init__(
            module_type,
            container=parent_container,
            name=get_name(module_type),
            config=config,
        )
        self._init_kwargs = build_init_kwargs(self.module, kwargs)
        self._register_module()

    def _validate_module_type(self) -> None:
        assert (
            type(self.module) is ModuleBaseMeta
        ), f"Module Type must be a subclass of ModuleBase;\n Invalid Type[{self.module}]"

    def _register_module(self) -> None:
        if not is_decorated_with_injectable(self.module):
            injectable()(self.module)

        self.add_provider(
            ProviderConfig(
                self.module,
                use_value=ModuleProvider(self.module, **self._init_kwargs),
                tag=self.name,
            ),
            export=True,
        )
