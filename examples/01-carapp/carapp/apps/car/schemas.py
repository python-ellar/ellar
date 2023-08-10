"""
Define Serializers/DTOs
Example:

class ASampleDTO(Serializer):
    name: str
    age: t.Optional[int] = None

for dataclasses, Inherit from DataclassSerializer

@dataclass
class ASampleDTO(DataclassSerializer):
    name: str
    age: t.Optional[int] = None
"""
from ellar.common.serializer import Serializer
from pydantic import Field


class CreateCarSerializer(Serializer):
    name: str
    year: int = Field(..., gt=0)
    model: str


class CarListFilter(Serializer):
    offset: int = 1
    limit: int = 10


class CarSerializer(Serializer):
    id: str
    name: str
    year: int
    model: str
