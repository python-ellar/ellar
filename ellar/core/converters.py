import typing as t
from abc import ABC, abstractmethod

from pydantic.typing import get_args, get_origin

_origin_maps = {
    list: t.List,
    tuple: t.Tuple,
    set: t.Set,
    dict: t.Dict,
    t.List: t.List,
    t.Tuple: t.Tuple,
    t.Set: t.Set,
    t.Dict: t.Dict,
    t.Optional: t.Optional,
    t.Union: t.Union,
}


@t.no_type_check
def _get_origin(outer_type_: t.Any) -> object:
    outer_type_origin = get_origin(outer_type_)
    return _origin_maps.get(outer_type_origin, outer_type_origin)


class TypeDefinitionConverter(ABC):
    def __init__(self, outer_type_: t.Any) -> None:
        self.type_origin = _get_origin(outer_type_)
        self.sub_fields = self.get_sub_fields(get_args(outer_type_))
        self.response_object = None
        if not self.sub_fields and not self.type_origin:
            self.response_object = self.get_modified_type(outer_type_)

    @abstractmethod
    def get_modified_type(
        self, outer_type_: t.Any
    ) -> t.Type[t.Any]:  # pragma: no cover
        ...

    def get_sub_fields(
        self, sub_fields: t.Tuple[t.Any, ...]
    ) -> t.List["TypeDefinitionConverter"]:
        _sub_fields = []
        for field in sub_fields or []:
            _sub_fields.append(self.__class__(field))
        return _sub_fields

    def re_group_outer_type(self) -> t.Any:
        if self.response_object:
            return self.response_object

        sub_fields = [field.re_group_outer_type() for field in self.sub_fields]
        return self.type_origin[tuple(sub_fields)]

    def __repr__(self) -> str:  # pragma: no cover
        return f"<type_origin='{self.type_origin}', sub-fields='{len(self.sub_fields)}'"
