"""
Create a provider and declare its scope

@injectable
class AProvider
    pass

@injectable(scope=transient_scope)
class BProvider
    pass
"""
import typing as t
import uuid

from ellar.di import injectable, singleton_scope


class DummyDBItem:
    pk: str

    def __init__(self, **data: t.Dict) -> None:
        self.__dict__ = data

    def __eq__(self, other):
        if isinstance(other, DummyDBItem):
            return self.pk == other.pk
        return self.pk == str(other)


@injectable(scope=singleton_scope)
class CarDummyDB:
    def __init__(self) -> None:
        self._data: t.List[DummyDBItem] = []

    def add_car(self, data: t.Dict) -> str:
        pk = uuid.uuid4()
        _data = dict(data)
        _data.update(pk=str(pk))
        item = DummyDBItem(**_data)
        self._data.append(item)
        return item.pk

    def list(self) -> t.List[DummyDBItem]:
        return self._data

    def update(self, car_id: str, data: t.Dict) -> t.Optional[DummyDBItem]:
        if car_id in self._data:
            idx = self._data.index(car_id)
            _data = dict(data)
            _data.update(pk=str(car_id))
            self._data[idx] = DummyDBItem(**_data)
            return self._data[idx]

    def get(self, car_id: str) -> t.Optional[DummyDBItem]:
        if car_id in self._data:
            idx = self._data.index(car_id)
            return self._data[idx]

    def remove(self, car_id: str) -> t.Optional[DummyDBItem]:
        if car_id in self._data:
            idx = self._data.index(car_id)
            return self._data.pop(idx)
