import typing as t

from ellar.common import ModuleRouter
from ellar.common.constants import CONTROLLER_OPERATION_HANDLER_KEY
from ellar.core.routing import EllarMount
from ellar.core.routing.utils import build_route_parameters
from ellar.reflect import reflect

from .base import RouterBuilder

T_ = t.TypeVar("T_")


class ModuleRouterBuilder(RouterBuilder, controller_type=ModuleRouter):
    @classmethod
    def build(
        cls,
        controller_type: t.Union[ModuleRouter, t.Any],
        base_route_type: t.Type[t.Union[EllarMount, T_]] = EllarMount,
        **kwargs: t.Any,
    ) -> t.Union[T_, EllarMount]:
        if controller_type.get_pre_build_routes():
            routes = build_route_parameters(
                controller_type.get_pre_build_routes(), controller_type.control_type
            )
        else:
            routes = reflect.get_metadata(
                CONTROLLER_OPERATION_HANDLER_KEY, controller_type.control_type
            )

        controller_type.clear_pre_build_routes()
        return base_route_type(**controller_type.get_mount_init(), routes=routes)  # type:ignore[call-arg]

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert isinstance(controller_type, ModuleRouter)
