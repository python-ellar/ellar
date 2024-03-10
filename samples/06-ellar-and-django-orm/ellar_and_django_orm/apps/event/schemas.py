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

from datetime import date

from ellar.common import Serializer


class EventSchemaIn(Serializer):
    title: str
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


class EventSchemaOut(Serializer):
    id: int
    title: str
    start_date: date
    end_date: date
