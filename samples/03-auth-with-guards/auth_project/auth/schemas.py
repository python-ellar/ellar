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
from dataclasses import dataclass

from ellar.common import DataclassSerializer


@dataclass
class UserCredentials(DataclassSerializer):
    username: str
    password: str
