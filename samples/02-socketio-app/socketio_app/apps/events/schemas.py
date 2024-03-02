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
import typing as t

from ellar.common import Serializer


class MessageData(Serializer):
    data: t.Any


class MessageRoom(Serializer):
    room: str


class MessageChatRoom(Serializer):
    room: str
    data: t.Any
