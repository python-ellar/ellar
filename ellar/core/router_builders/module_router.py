import typing as t

from ellar.common import ModuleRouter
from ellar.common.compatible import AttributeDict
from ellar.common.constants import CONTROLLER_METADATA, CONTROLLER_OPERATION_HANDLER_KEY
from ellar.common.shortcuts import normalize_path
from ellar.core.routing import EllarMount
from ellar.reflect import reflect

from .base import RouterBuilder
from .utils import build_route_parameters, process_nested_routes

T_ = t.TypeVar("T_")


class ModuleRouterBuilder(RouterBuilder, controller_type=ModuleRouter):
    @classmethod
    def build(
        cls,
        controller_type: t.Union[ModuleRouter, t.Any],
        base_route_type: t.Type[t.Union[EllarMount, T_]] = EllarMount,
        **kwargs: t.Any,
    ) -> t.Union[T_, EllarMount]:
        if reflect.get_metadata(
            CONTROLLER_METADATA.PROCESSED, controller_type.control_type
        ):
            routes = reflect.get_metadata(
                CONTROLLER_OPERATION_HANDLER_KEY, controller_type.control_type
            )
        else:
            routes = build_route_parameters(
                controller_type.get_pre_build_routes(), controller_type.control_type
            )
            routes.extend(process_nested_routes(controller_type.control_type))

        init_kwargs = AttributeDict(controller_type.get_mount_init())

        if "prefix" in kwargs:
            prefix = kwargs.pop("prefix")
            init_kwargs.path = normalize_path(f"{prefix}/{init_kwargs.path}")

        controller_type.clear_pre_build_routes()
        router = base_route_type(**init_kwargs, routes=routes)  # type:ignore[call-arg]

        reflect.define_metadata(
            CONTROLLER_METADATA.PROCESSED, True, controller_type.control_type
        )
        return router

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert isinstance(controller_type, ModuleRouter)
