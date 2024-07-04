import dataclasses
import typing as t

from ellar.common.constants import NESTED_ROUTERS_KEY
from ellar.common.interfaces import IExecutionContext
from ellar.reflect import reflect

if t.TYPE_CHECKING:
    from ellar.common.operations import ModuleRouter


@dataclasses.dataclass
class NestedRouterInfo:
    router: t.Union["ModuleRouter", t.Type["ControllerBase"]]
    prefix: t.Optional[str] = None


class ControllerType(type):
    _controller_name: t.Optional[str]

    def controller_class_name(cls) -> str:
        """ """
        if cls._controller_name:
            return cls._controller_name
        return cls.__name__.lower().replace("controller", "")

    def full_view_name(cls, name: str) -> str:
        """ """
        return f"{cls.controller_class_name()}/{name}"

    def add_router(
        cls,
        router: t.Union[t.Type["ControllerBase"], "ModuleRouter"],
        prefix: t.Optional[str] = None,
    ) -> None:
        if prefix:
            assert prefix.startswith("/"), "'prefix' must start with '/'"

        reflect.define_metadata(
            NESTED_ROUTERS_KEY, [NestedRouterInfo(prefix=prefix, router=router)], cls
        )


class ControllerBase(metaclass=ControllerType):
    # `context` variable will change based on the route function called on the APIController
    # that way we can get some specific items things that belong the route function during execution
    context: t.Optional[IExecutionContext] = None

    @t.no_type_check
    def __init_subclass__(cls, controller_name: str = None) -> None:
        cls._controller_name = controller_name
