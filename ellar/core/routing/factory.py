import typing as t

from ellar.common.constants import (
    CONTROLLER_METADATA,
    CONTROLLER_OPERATION_HANDLER_KEY,
    CONTROLLER_WATERMARK,
)
from ellar.common.models import ControllerBase, ControllerType
from ellar.common.routing import ModuleMount, RouteCollection
from ellar.reflect import reflect
from starlette.routing import Router

from .builder import RouterBuilder


class ControllerRouterFactory(RouterBuilder, controller_type=type(ControllerBase)):
    @classmethod
    def build(
        cls, controller_type: t.Union[t.Type[ControllerBase], t.Any], **kwargs: t.Any
    ) -> ModuleMount:
        routes = (
            reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, controller_type)
            or []
        )

        app = Router()
        app.routes = RouteCollection(routes)  # type:ignore

        include_in_schema = reflect.get_metadata_or_raise_exception(
            CONTROLLER_METADATA.INCLUDE_IN_SCHEMA, controller_type
        )
        router = ModuleMount(
            app=app,
            path=reflect.get_metadata_or_raise_exception(
                CONTROLLER_METADATA.PATH, controller_type
            ),
            name=reflect.get_metadata_or_raise_exception(
                CONTROLLER_METADATA.NAME, controller_type
            ),
            include_in_schema=include_in_schema
            if include_in_schema is not None
            else True,
            control_type=controller_type,
            **kwargs,
        )
        return router

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert reflect.get_metadata(
            CONTROLLER_WATERMARK, controller_type
        ) and isinstance(controller_type, ControllerType), "Invalid Controller Type."
