import typing as t
from types import FunctionType

from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_OPERATION_HANDLER_KEY,
    ROUTE_OPERATION_PARAMETERS,
)
from ellar.common.logging import logger
from ellar.common.operations import RouteParameters, WsRouteParameters
from ellar.reflect import reflect
from ellar.utils import get_unique_type

from .base import RouteOperationBase
from .route import RouteOperation
from .websocket import WebsocketRouteOperation


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
) -> t.List[RouteOperationBase]:
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
