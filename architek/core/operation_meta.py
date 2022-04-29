import typing as t

from architek.compatible import AttributeDict
from architek.constants import (
    EXTRA_ROUTE_ARGS_KEY,
    GUARDS_KEY,
    OPENAPI_KEY,
    RESPONSE_OVERRIDE_KEY,
    VERSIONING_KEY,
)

if t.TYPE_CHECKING:
    from architek.core.guard import GuardCanActivate
    from architek.core.params import ExtraEndpointArg


class OperationMeta(AttributeDict):
    extra_route_args: t.List["ExtraEndpointArg"]
    response_override: t.Union[AttributeDict[int, t.Union[t.Type, t.Any]], t.Type]
    route_versioning: t.Set[t.Union[int, float, str]]
    route_guards: t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
    openapi: AttributeDict

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        kwargs.setdefault(EXTRA_ROUTE_ARGS_KEY, [])
        kwargs.setdefault(RESPONSE_OVERRIDE_KEY, AttributeDict())
        kwargs.setdefault(VERSIONING_KEY, set())
        kwargs.setdefault(GUARDS_KEY, [])
        kwargs.setdefault(OPENAPI_KEY, AttributeDict())
        super(OperationMeta, self).__init__(*args, **kwargs)

    def __deepcopy__(self, memodict: t.Dict = {}) -> "OperationMeta":
        return self.__copy__(memodict)

    def __copy__(self, memodict: t.Dict = {}) -> "OperationMeta":
        return OperationMeta(**self)
