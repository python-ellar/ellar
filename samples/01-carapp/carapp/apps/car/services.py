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

from ellar.di import injectable, singleton_scope

from .schemas import CarSerializer, CreateCarSerializer


@injectable(scope=singleton_scope)
class CarRepository:
    def __init__(self):
        self._cars: t.List[CarSerializer] = []

    def create_car(self, data: CreateCarSerializer) -> dict:
        data = CarSerializer(id=len(self._cars) + 1, **data.dict())
        self._cars.append(data)
        return data.dict()

    def get_all(self) -> t.List[CarSerializer]:
        return self._cars
