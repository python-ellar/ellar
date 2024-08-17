import typing as t

from ellar.common import constants
from ellar.common.logging import logger
from ellar.common.models.controller import ControllerBase, ControllerType
from ellar.common.operations import RouteParameters, WsRouteParameters
from ellar.common.shortcuts import normalize_path
from ellar.core.routing import (
    ControllerRouteOperation,
    ControllerWebsocketRouteOperation,
    EllarControllerMount,
)
from ellar.reflect import reflect
from starlette.routing import BaseRoute

from ...utils import get_functions_with_tag
from .base import RouterBuilder
from .utils import process_nested_routes

T_ = t.TypeVar("T_")


def process_controller_routes(controller: t.Type[ControllerBase]) -> t.List[BaseRoute]:
    res: t.List[BaseRoute] = []

    if reflect.get_metadata(constants.CONTROLLER_METADATA.PROCESSED, controller):
        return (
            reflect.get_metadata(constants.CONTROLLER_OPERATION_HANDLER_KEY, controller)
            or []
        )

    for _, item in get_functions_with_tag(
        controller, tag=constants.OPERATION_ENDPOINT_KEY
    ):
        parameters = item.__dict__[constants.ROUTE_OPERATION_PARAMETERS]
        operation: t.Union[ControllerRouteOperation, ControllerWebsocketRouteOperation]

        if not isinstance(parameters, list):
            parameters = [parameters]

        for parameter in parameters:
            if isinstance(parameter, RouteParameters):
                operation = ControllerRouteOperation(
                    **parameter.dict(), controller=controller
                )
            elif isinstance(parameter, WsRouteParameters):
                operation = ControllerWebsocketRouteOperation(
                    **parameter.dict(), controller=controller
                )
            else:  # pragma: no cover
                logger.warning(
                    f"Parameter type is not recognized. {type(parameter) if not isinstance(parameter, type) else parameter}"
                )
                continue

            reflect.define_metadata(
                constants.CONTROLLER_OPERATION_HANDLER_KEY,
                [operation],
                controller,
            )
            res.append(operation)
    return res


class ControllerRouterBuilder(RouterBuilder, controller_type=type(ControllerBase)):
    @classmethod
    def build(
        cls,
        controller_type: t.Union[t.Type[ControllerBase], t.Any],
        base_route_type: t.Type[
            t.Union[EllarControllerMount, T_]
        ] = EllarControllerMount,
        **kwargs: t.Any,
    ) -> t.Union[T_, EllarControllerMount]:
        routes = process_controller_routes(controller_type)
        routes.extend(process_nested_routes(controller_type))

        include_in_schema = reflect.get_metadata_or_raise_exception(
            constants.CONTROLLER_METADATA.INCLUDE_IN_SCHEMA, controller_type
        )

        middleware = reflect.get_metadata(
            constants.CONTROLLER_METADATA.MIDDLEWARE, controller_type
        )

        kwargs.update(middleware=middleware)

        path = reflect.get_metadata_or_raise_exception(
            constants.CONTROLLER_METADATA.PATH, controller_type
        )

        if "prefix" in kwargs:
            prefix = kwargs.pop("prefix")
            path = normalize_path(f"{prefix}/{path}")

        router = base_route_type(  # type:ignore[call-arg]
            routes=routes,
            path=path,
            name=reflect.get_metadata_or_raise_exception(
                constants.CONTROLLER_METADATA.NAME, controller_type
            ),
            include_in_schema=include_in_schema
            if include_in_schema is not None
            else True,
            **kwargs,
        )
        reflect.define_metadata(
            constants.CONTROLLER_METADATA.PROCESSED, True, controller_type
        )
        reflect.define_metadata(constants.CONTROLLER_CLASS_KEY, controller_type, router)
        return router

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert reflect.get_metadata(
            constants.CONTROLLER_WATERMARK, controller_type
        ) and isinstance(controller_type, ControllerType), "Invalid Controller Type."
