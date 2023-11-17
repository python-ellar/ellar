import typing as t
from types import FunctionType

from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_OPERATION_HANDLER_KEY,
    ROUTE_OPERATION_PARAMETERS,
)
from ellar.common.logger import logger
from ellar.common.routing import (
    RouteOperation,
    RouteOperationBase,
    WebsocketRouteOperation,
)
from ellar.common.routing.schema import RouteParameters, WsRouteParameters
from ellar.common.utils import get_unique_control_type
from ellar.reflect import reflect


@t.no_type_check
def build_route_handler(item: t.Callable) -> t.Optional[RouteOperationBase]:
    _item: t.Any = item

    if callable(item) and type(item) == FunctionType:
        _item = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, item)

    if not _item and not reflect.has_metadata(CONTROLLER_CLASS_KEY, item):
        reflect.define_metadata(CONTROLLER_CLASS_KEY, get_unique_control_type(), item)

    if not _item and hasattr(item, ROUTE_OPERATION_PARAMETERS):
        operations = build_route_parameters([item.__dict__[ROUTE_OPERATION_PARAMETERS]])
        if not operations:
            return None  # pragma: no cover
        return operations[0]
    return _item


@t.no_type_check
def build_route_parameters(
    items: t.List[t.Union[RouteParameters, WsRouteParameters]]
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
    return results
