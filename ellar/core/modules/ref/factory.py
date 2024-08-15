import typing as t

from ellar.common.constants import MODULE_WATERMARK
from ellar.core.modules.base import ModuleBase, ModuleBaseMeta
from ellar.di import Container
from ellar.reflect import reflect

from .base import ModuleRefBase
from .plain import ModulePlainRef
from .template import ModuleTemplateRef

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core import Config


class InvalidModuleTypeException(Exception):
    pass


def create_module_ref_factor(
    module_type: t.Union[t.Type, t.Type[ModuleBase]],
    config: "Config",
    container: t.Optional[Container] = None,
    **init_kwargs: t.Any,
) -> t.Union["ModuleRefBase", "ModuleTemplateRef"]:
    module_ref: t.Union["ModuleRefBase", "ModuleTemplateRef"]
    if reflect.get_metadata(MODULE_WATERMARK, module_type):
        module_ref = ModuleTemplateRef(
            module_type,
            parent_container=container,
            config=config,
            **init_kwargs,
        )
        return module_ref
    elif type(module_type) is ModuleBaseMeta:
        assert (
            container is not None
        ), "ModulePlainRef class can't take a nullable 'container'"

        module_ref = ModulePlainRef(
            module_type,
            parent_container=container,
            config=config,
            **init_kwargs,
        )
        return module_ref

    raise InvalidModuleTypeException(
        f"{module_type.__name__} must be a subclass of `ellar.core.ModuleBase`"
    )
