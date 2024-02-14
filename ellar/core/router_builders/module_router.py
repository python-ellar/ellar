import typing as t

from ellar.common import ModuleRouter
from ellar.common.constants import CONTROLLER_OPERATION_HANDLER_KEY
from ellar.core.routing import EllarMount, RouteCollection
from ellar.core.routing.utils import build_route_parameters
from ellar.reflect import reflect
from starlette.routing import Router

from .base import RouterBuilder


class ModuleRouterBuilder(RouterBuilder, controller_type=ModuleRouter):
    @classmethod
    def build(
        cls, controller_type: t.Union[ModuleRouter, t.Any], **kwargs: t.Any
    ) -> EllarMount:
        if controller_type.get_pre_build_routes():
            routes = build_route_parameters(
                controller_type.get_pre_build_routes(), controller_type.control_type
            )
        else:
            routes = reflect.get_metadata(
                CONTROLLER_OPERATION_HANDLER_KEY, controller_type.control_type
            )

        app = Router()
        app.routes = RouteCollection(routes)  # type:ignore

        controller_type.clear_pre_build_routes()
        return EllarMount(**controller_type.get_mount_init(), app=app)

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert isinstance(controller_type, ModuleRouter)
