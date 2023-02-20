import pickle
import typing as t
from abc import ABC, abstractmethod


class IRedisSerializer(ABC):
    default_protocol: int = pickle.HIGHEST_PROTOCOL

    @abstractmethod
    def load(self, data: t.Any) -> t.Any:  # pragma: no cover
        ...

    @abstractmethod
    def dumps(self, data: t.Any) -> t.Any:  # pragma: no cover
        ...


class RedisSerializer(IRedisSerializer):
    def __init__(self, protocol: int = None) -> None:
        self._protocol = protocol or self.default_protocol

    def load(self, data: t.Any) -> t.Any:
        try:
            return int(data)
        except ValueError:
            return pickle.loads(data)

    def dumps(self, data: t.Any) -> t.Any:
        # Only skip pickling for integers, an int subclasses as bool should be
        # pickled.
        if type(data) is int:
            return data
        return pickle.dumps(data, self._protocol)
