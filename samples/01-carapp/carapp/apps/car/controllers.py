"""
Define endpoints routes in python class-based fashion
example:

@Controller("/dogs", tag="Dogs", description="Dogs Resources")
class MyController(ControllerBase):
    @get('/')
    def index(self):
        return {'detail': "Welcome Dog's Resources"}
"""
import typing_extensions as types
from ellar.common import (
    Body,
    Controller,
    ControllerBase,
    Query,
    Version,
    get,
    post,
    render,
)
from ellar.openapi import ApiTags

from .schemas import CarListFilter, CreateCarSerializer
from .services import CarRepository


@Controller("/car")
@ApiTags(
    description="Example of Car Resource with <strong>Controller</strong>",
    name="CarController",
)
class CarController(ControllerBase):
    def __init__(self, repo: CarRepository):
        self.repo = repo

    @get("/list-html")
    @render()
    async def list(self):
        return self.repo.get_all()

    @post()
    async def create(self, payload: types.Annotated[CreateCarSerializer, Body()]):
        result = self.repo.create_car(payload)
        result.update(message="This action adds a new car")
        return result

    @get("/{car_id:str}")
    async def get_one(self, car_id: str):
        return f"This action returns a #{car_id} car"

    @get()
    async def get_all(self, query: CarListFilter = Query()):
        res = {
            "cars": self.repo.get_all(),
            "message": f"This action returns all cars at limit={query.limit}, offset={query.offset}",
        }
        return res

    @post("/", name="v2_create")
    @Version("v2")
    async def create_v2(self, payload: Body[CreateCarSerializer]):
        result = self.repo.create_car(payload)
        result.update(message="This action adds a new car - version 2")
        return result
