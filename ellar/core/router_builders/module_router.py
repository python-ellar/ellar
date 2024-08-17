import typing as t

from ellar.common import ModuleRouter, constants
from ellar.common.compatible import AttributeDict
from ellar.common.shortcuts import normalize_path
from ellar.core.routing import EllarControllerMount
from ellar.reflect import reflect

from .base import RouterBuilder
from .utils import build_route_parameters, process_nested_routes

T_ = t.TypeVar("T_")


class ModuleRouterBuilder(RouterBuilder, controller_type=ModuleRouter):
    @classmethod
    def build(
        cls,
        controller_type: t.Union[ModuleRouter, t.Any],
        base_route_type: t.Type[
            t.Union[EllarControllerMount, T_]
        ] = EllarControllerMount,
        **kwargs: t.Any,
    ) -> t.Union[T_, EllarControllerMount]:
        pre_build_routes = (
            reflect.get_metadata(
                constants.ROUTER_PRE_BUILD_ROUTES, target=controller_type
            )
            or []
        )
        if len(pre_build_routes) > 0:
            routes = build_route_parameters(
                pre_build_routes,
                controller_type=controller_type,
            )
            routes.extend(process_nested_routes(controller_type))
            reflect.delete_metadata(
                constants.ROUTER_PRE_BUILD_ROUTES, target=controller_type
            )
        else:
            routes = reflect.get_metadata(
                constants.CONTROLLER_OPERATION_HANDLER_KEY, controller_type
            )

        init_kwargs = AttributeDict(
            {
                "path": controller_type.path,
                "name": controller_type.name,
                "include_in_schema": controller_type.include_in_schema,
                # "control_type": self.get_controller_type(),
                "middleware": controller_type.middleware,
            }
        )

        if "prefix" in kwargs:
            prefix = kwargs.pop("prefix")
            init_kwargs.path = normalize_path(f"{prefix}/{init_kwargs.path}")

        router = base_route_type(**init_kwargs, routes=routes)  # type:ignore[call-arg]
        reflect.define_metadata(constants.CONTROLLER_CLASS_KEY, controller_type, router)
        return router

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert isinstance(controller_type, ModuleRouter)
