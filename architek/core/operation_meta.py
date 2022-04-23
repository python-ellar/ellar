import typing as t

from architek.core.compatible import AttributeDictAccess
from architek.types import KT, VT

if t.TYPE_CHECKING:
    from architek.core.guard import GuardCanActivate
    from architek.core.params import ExtraEndpointArg


class _AttributeDict(AttributeDictAccess, t.Dict[KT, VT]):
    def __getattr__(self, name: KT) -> t.Optional[VT]:  # type: ignore
        value = self.get(name)
        return value

    def set_defaults(self, **kwargs: t.Any) -> None:
        for k, v in kwargs.items():
            self.setdefault(k, v)  # type: ignore


class OperationMeta(_AttributeDict):
    extra_route_args: t.List["ExtraEndpointArg"]
    response_override: t.Union[_AttributeDict[int, t.Union[t.Type, t.Any]], t.Type]
    route_versioning: t.Set[t.Union[int, float, str]]
    route_guards: t.List[t.Union[t.Type["GuardCanActivate"], "GuardCanActivate"]]
    openapi: _AttributeDict

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        kwargs.setdefault("extra_route_args", [])
        kwargs.setdefault("response_override", _AttributeDict())
        kwargs.setdefault("route_versioning", set())
        kwargs.setdefault("route_guards", [])
        kwargs.setdefault("openapi", _AttributeDict())
        super(OperationMeta, self).__init__(*args, **kwargs)

    def __deepcopy__(self, memodict: t.Dict = {}) -> "OperationMeta":
        return self.__copy__(memodict)

    def __copy__(self, memodict: t.Dict = {}) -> "OperationMeta":
        return OperationMeta(**self)
