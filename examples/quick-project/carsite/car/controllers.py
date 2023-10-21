"""
Define endpoints routes in python class-based fashion
example:

@Controller("/dogs", tag="Dogs", description="Dogs Resources")
class MyController(ControllerBase):
    @get('/')
    def index(self):
        return {'detail': "Welcome Dog's Resources"}
"""
import typing as t

from ellar.common import Controller, ControllerBase, delete, get, post, put
from ellar.common.exceptions import NotFound

from .schemas import CarSerializer, RetrieveCarSerializer
from .services import CarDummyDB


@Controller
class CarController(ControllerBase):
    def __init__(self, db: CarDummyDB) -> None:
        self.car_db = db

    @post("/create", response={200: str})
    async def create_cat(self, payload: CarSerializer):
        pk = self.car_db.add_car(payload.dict())
        return pk

    @put("/{car_id:str}", response={200: RetrieveCarSerializer})
    async def update_cat(self, car_id: str, payload: CarSerializer):
        car = self.car_db.update(car_id, payload.dict())
        if not car:
            raise NotFound("Item not found")
        return car

    @get("/{car_id:str}", response={200: RetrieveCarSerializer})
    async def get_car_by_id(self, car_id: str):
        car = self.car_db.get(car_id)
        if not car:
            raise NotFound("Item not found.")
        return car

    @delete("/{car_id:str}", response={204: dict})
    async def deleted_cat(self, car_id: str):
        car = self.car_db.remove(car_id)
        if not car:
            raise NotFound("Item not found.")
        return 204, {}

    @get("/", response={200: t.List[RetrieveCarSerializer]})
    async def list(self):
        return self.car_db.list()
