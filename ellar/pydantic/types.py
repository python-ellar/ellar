import types
import typing as t

from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined, PydanticUndefinedType
from pydantic_core import Url as Url

UnionType = getattr(types, "UnionType", t.Union)
NoneType = getattr(types, "NoneType", type(None))
FieldInfoType = t.TypeVar("FieldInfoType", bound=FieldInfo)

IncEx = t.Union[t.Set[int], t.Set[str], t.Dict[int, t.Any], t.Dict[str, t.Any]]

Required = PydanticUndefined
Undefined = PydanticUndefined
UndefinedType = PydanticUndefinedType
Validator = t.Any
AnyUrl = Url
