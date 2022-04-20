import typing as t

from architek.types import KT, VT


class AttributeDictAccess:
    def __getattr__(self, name) -> VT:
        if name in self:
            value = self.get(name)
            return value
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class DataMapper(t.Mapping, t.Generic[KT, VT]):
    __slots__ = ("_data",)

    def __init__(self, **data: t.Any) -> None:
        self._data: t.Union[t.Dict, t.Any] = dict(data)

    def __contains__(self, item: KT) -> bool:
        return item in self._data

    def __getitem__(self, k: KT) -> VT:
        return self._data.__getitem__(k)

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> t.Iterator[VT]:
        return iter(self._data)


class DataMutableMapper(DataMapper, t.MutableMapping[KT, VT]):
    def __setitem__(self, k: KT, v: VT) -> None:
        self._data.__setitem__(k, v)

    def __delitem__(self, v: KT) -> None:
        self._data.__delitem__(v)
