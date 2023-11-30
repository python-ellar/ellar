import types
import typing as t

from pydantic_core import PydanticUndefined, PydanticUndefinedType
from pydantic_core import Url as Url

UnionType = getattr(types, "UnionType", t.Union)
IncEx = t.Union[t.Set[int], t.Set[str], t.Dict[int, t.Any], t.Dict[str, t.Any]]


Required = PydanticUndefined
Undefined = PydanticUndefined
UndefinedType = PydanticUndefinedType
Validator = t.Any
AnyUrl = Url
