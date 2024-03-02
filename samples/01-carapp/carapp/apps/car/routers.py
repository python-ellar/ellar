"""
Define endpoints routes in python function fashion
example:

my_router = ModuleRouter("/cats", tag="Cats", description="Cats Resource description")

@my_router.get('/')
def index(request: Request):
    return {'detail': 'Welcome to Cats Resource'}
"""

from dataclasses import dataclass
from typing import List

from ellar.common import (
    Inject,
    ModuleRouter,
    render,
    render_template,
)
from ellar.core import Request
from ellar.openapi import ApiTags

from .services import CarRepository

router = ModuleRouter("/car-as-router")
ApiTags(
    name="Router",
    description="Example of Car Resource from a <strong>ModuleRouter</strong>",
)(router)


@dataclass
class CarObject:
    name: str
    model: str


@router.get(response={200: List[CarObject]})
async def get_cars(repo: Inject[CarRepository]):
    return repo.get_all()


@router.http_route("/html", methods=["get", "post"])
@render("index.html")
async def get_car_html(repo: Inject[CarRepository]):
    return repo.get_all()


@router.get("/html/outside")
async def get_car_html_with_render(
    repo: Inject[CarRepository], request: Inject[Request]
):
    return render_template("car/list.html", request=request, model=repo.get_all())
