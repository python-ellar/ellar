import typing as t

from ellar.di import MODULE_REF_TYPES

if t.TYPE_CHECKING:
    from .base import ModuleRefBase


class ModuleForwardRef:
    __slots__ = ("_module_ref",)

    ref_type: str = MODULE_REF_TYPES.FORWARD_REF

    def __init__(self, module_ref: "ModuleRefBase") -> None:
        self._module_ref = module_ref

    def __getattr__(self, item: t.Any) -> t.Any:
        return getattr(self._module_ref, item)

    def __hash__(self) -> int:
        return hash((self._module_ref.module, "ForwardRef"))

    def __eq__(self, other: t.Union[t.Any, "ModuleForwardRef"]) -> bool:
        if isinstance(other, ModuleForwardRef):
            return self._module_ref is other._module_ref
        return False
