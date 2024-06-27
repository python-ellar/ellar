import typing as t

from ellar.common.constants import (
    CONTROLLER_METADATA,
    CONTROLLER_OPERATION_HANDLER_KEY,
    CONTROLLER_WATERMARK,
    OPERATION_ENDPOINT_KEY,
    ROUTE_OPERATION_PARAMETERS,
)
from ellar.common.logging import logger
from ellar.common.models.controller import ControllerBase, ControllerType
from ellar.common.operations import RouteParameters, WsRouteParameters
from ellar.common.shortcuts import normalize_path
from ellar.core.routing import (
    ControllerRouteOperation,
    ControllerWebsocketRouteOperation,
    EllarMount,
)
from ellar.reflect import reflect
from starlette.routing import BaseRoute

from ...utils import get_functions_with_tag
from .base import RouterBuilder
from .utils import process_nested_routes

T_ = t.TypeVar("T_")


def process_controller_routes(controller: t.Type[ControllerBase]) -> t.List[BaseRoute]:
    res: t.List[BaseRoute] = []

    if reflect.get_metadata(CONTROLLER_METADATA.PROCESSED, controller):
        return reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, controller) or []

    for _, item in get_functions_with_tag(controller, tag=OPERATION_ENDPOINT_KEY):
        parameters = item.__dict__[ROUTE_OPERATION_PARAMETERS]
        operation: t.Union[ControllerRouteOperation, ControllerWebsocketRouteOperation]

        if not isinstance(parameters, list):
            parameters = [parameters]

        for parameter in parameters:
            if isinstance(parameter, RouteParameters):
                operation = ControllerRouteOperation(controller, **parameter.dict())
            elif isinstance(parameter, WsRouteParameters):
                operation = ControllerWebsocketRouteOperation(
                    controller, **parameter.dict()
                )
            else:  # pragma: no cover
                logger.warning(
                    f"Parameter type is not recognized. {type(parameter) if not isinstance(parameter, type) else parameter}"
                )
                continue

            reflect.define_metadata(
                CONTROLLER_OPERATION_HANDLER_KEY,
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
        base_route_type: t.Type[t.Union[EllarMount, T_]] = EllarMount,
        **kwargs: t.Any,
    ) -> t.Union[T_, EllarMount]:
        routes = process_controller_routes(controller_type)
        routes.extend(process_nested_routes(controller_type))

        include_in_schema = reflect.get_metadata_or_raise_exception(
            CONTROLLER_METADATA.INCLUDE_IN_SCHEMA, controller_type
        )

        middleware = reflect.get_metadata(
            CONTROLLER_METADATA.MIDDLEWARE, controller_type
        )

        kwargs.setdefault("middleware", middleware)

        path = reflect.get_metadata_or_raise_exception(
            CONTROLLER_METADATA.PATH, controller_type
        )

        if "prefix" in kwargs:
            prefix = kwargs.pop("prefix")
            path = normalize_path(f"{prefix}/{path}")

        router = base_route_type(  # type:ignore[call-arg]
            routes=routes,
            path=path,
            name=reflect.get_metadata_or_raise_exception(
                CONTROLLER_METADATA.NAME, controller_type
            ),
            include_in_schema=include_in_schema
            if include_in_schema is not None
            else True,
            control_type=controller_type,
            **kwargs,
        )
        reflect.define_metadata(CONTROLLER_METADATA.PROCESSED, True, controller_type)
        return router

    @classmethod
    def check_type(cls, controller_type: t.Union[t.Type, t.Any]) -> None:
        assert reflect.get_metadata(
            CONTROLLER_WATERMARK, controller_type
        ) and isinstance(controller_type, ControllerType), "Invalid Controller Type."
