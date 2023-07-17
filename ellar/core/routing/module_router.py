import typing as t

from ellar.common import ModuleRouter
from ellar.common.routing import ModuleMount

from .builder import RouterBuilder
from .helper import build_route_parameters


class ModuleRouterFactory(RouterBuilder, controller_type=ModuleRouter):
    @classmethod
    def build(
        cls, controller_type: t.Union[ModuleRouter, t.Any], **kwargs: t.Any
    ) -> ModuleMount:
        if controller_type.get_pre_build_routes():
            results = build_route_parameters(controller_type.get_pre_build_routes())
            controller_type.app.routes.extend(results)  # type:ignore
            controller_type.clear_pre_build_routes()
        return controller_type

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert isinstance(controller_type, ModuleRouter)
