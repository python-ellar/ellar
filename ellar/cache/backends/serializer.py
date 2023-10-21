import pickle
import typing as t
from abc import ABC, abstractmethod


class ICacheSerializer(ABC):
    default_protocol: int = pickle.HIGHEST_PROTOCOL

    @abstractmethod
    def load(self, data: t.Any) -> t.Any:  # pragma: no cover
        ...

    @abstractmethod
    def dumps(self, data: t.Any) -> t.Any:  # pragma: no cover
        ...


class RedisSerializer(ICacheSerializer):
    def __init__(self, protocol: t.Optional[int] = None) -> None:
        self._protocol = protocol or self.default_protocol

    def load(self, data: t.Any) -> t.Any:
        try:
            return int(data)
        except ValueError:
            return pickle.loads(data)

    def dumps(self, data: t.Any) -> t.Any:
        # Only skip pickling for integers, an int subclasses as bool should be
        # pickled.
        if isinstance(data, int):
            return data
        return pickle.dumps(data, self._protocol)


# class AioCacheSerializer(RedisSerializer):
#     def load(self, data: t.Any) -> t.Any:
#         try:
#             return int(data.decode("utf-8"))
#         except ValueError:
#             return pickle.loads(data)
#
#     def dumps(self, data: t.Any) -> t.Any:
#         # Only skip pickling for integers, an int subclasses as bool should be
#         # pickled.
#         if type(data) is int:
#             return str(data).encode("utf-8")
#         return pickle.dumps(data, self._protocol)
