from abc import ABC, abstractmethod
from typing import Type, Optional, List, Any

from pydantic.typing import get_origin, get_args


class TypeDefinitionConverter(ABC):
    def __init__(self, outer_type_: Type):
        self.type_origin = get_origin(outer_type_)
        self.sub_fields = self.get_sub_fields(get_args(outer_type_))
        self.response_object = None
        if not self.sub_fields and not self.type_origin:
            self.response_object = self.get_modified_type(outer_type_)

    @abstractmethod
    def get_modified_type(self, outer_type_: Type) -> Type[Any]:
        ...

    def get_sub_fields(self, sub_fields: Optional[List[Any]]) -> List['TypeDefinitionConverter']:
        _sub_fields = []
        for field in sub_fields or []:
            _sub_fields.append(self.__class__(field))
        return _sub_fields

    def re_group_outer_type(self) -> Type:
        if self.response_object:
            return self.response_object

        sub_fields = [field.re_group_outer_type() for field in self.sub_fields]
        return self.type_origin[tuple(sub_fields)]

    def __repr__(self):
        return f"<type_origin='{self.type_origin}', sub-fields='{len(self.sub_fields)}'"
