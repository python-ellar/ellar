import typing as t
from types import FunctionType

from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_METADATA,
    CONTROLLER_OPERATION_HANDLER_KEY,
    NESTED_ROUTERS_KEY,
    ROUTE_OPERATION_PARAMETERS,
)
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.logging import logger
from ellar.common.models.controller import NestedRouterInfo
from ellar.common.operations import RouteParameters, WsRouteParameters
from ellar.core.routing import (
    RouteOperation,
    RouteOperationBase,
    WebsocketRouteOperation,
)
from ellar.reflect import reflect
from ellar.utils import get_unique_type
from starlette.routing import BaseRoute

from .base import get_controller_builder_factory

T_ = t.TypeVar("T_")

_stack_cycle: t.Tuple = ()


def process_nested_routes(controller: t.Type[t.Any]) -> t.List[BaseRoute]:
    global _stack_cycle

    res: t.List[BaseRoute] = []

    if reflect.get_metadata(CONTROLLER_METADATA.PROCESSED, controller):
        return []

    if controller in _stack_cycle:
        raise ImproperConfiguration(
            "Circular Nested router detected: %s -> %s"
            % (" -> ".join(map(str, _stack_cycle)), controller)
        )

    _stack_cycle += (controller,)
    nested_routers: t.List[NestedRouterInfo] = (
        reflect.get_metadata(NESTED_ROUTERS_KEY, controller) or []
    )

    for item in nested_routers:
        kw = {"prefix": item.prefix} if item.prefix else {}

        factory_builder = get_controller_builder_factory(type(item.router))
        factory_builder.check_type(item.router)

        operation = factory_builder.build(item.router, **kw)
        reflect.define_metadata(
            CONTROLLER_OPERATION_HANDLER_KEY,
            [operation],
            controller,
        )

        res.append(operation)

    _stack_cycle = tuple(_stack_cycle[:-1])
    return res


@t.no_type_check
def build_route_handler(
    item: t.Union[t.Callable, t.Any],
) -> t.Optional[t.List[RouteOperationBase]]:
    _item: t.Any = item

    if callable(item) and type(item) == FunctionType:
        _item = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, item)

    if not _item and not reflect.has_metadata(CONTROLLER_CLASS_KEY, item):
        reflect.define_metadata(CONTROLLER_CLASS_KEY, get_unique_type(), item)

    if not _item and hasattr(item, ROUTE_OPERATION_PARAMETERS):
        parameters = item.__dict__[ROUTE_OPERATION_PARAMETERS]

        if not isinstance(parameters, list):
            parameters = [parameters]

        operations = build_route_parameters(parameters, get_unique_type())
        if isinstance(operations, list):
            return operations

    if _item:
        return [_item]

    return _item  # pragma: no cover


@t.no_type_check
def build_route_parameters(
    items: t.List[t.Union[RouteParameters, WsRouteParameters]],
    control_type: t.Type[t.Any],
) -> t.List[t.Union[RouteOperationBase, t.Any]]:
    results = []
    for item in items:
        if isinstance(item, RouteParameters):
            operation = RouteOperation(**item.dict())
        elif isinstance(item, WsRouteParameters):
            operation = WebsocketRouteOperation(**item.dict())
        else:  # pragma: no cover
            logger.warning(
                f"Parameter type is not recognized. {type(item) if not isinstance(item, type) else item}"
            )
            continue
        results.append(operation)

        if ROUTE_OPERATION_PARAMETERS in item.endpoint.__dict__:
            del item.endpoint.__dict__[ROUTE_OPERATION_PARAMETERS]

        reflect.define_metadata(
            CONTROLLER_OPERATION_HANDLER_KEY,
            [operation],
            control_type,
        )

    return results
