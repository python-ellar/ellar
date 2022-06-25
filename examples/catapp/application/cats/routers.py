from dataclasses import dataclass
from typing import List

from ellar.common import Provide, render, Req
from ellar.core.routing import ModuleRouter
from ellar.core.templating import render_template
from ellar.serializer import DataclassSerializer

from .services import CatService

cat_router = ModuleRouter("/cats-router", tag='Testing')


@dataclass
class CatObject(DataclassSerializer):
    name: str


@cat_router.get(response={200: List[CatObject]})
async def get_cats(request=Req(), service: CatService = Provide()):
    return service.list_cat()


@cat_router.http_route('/html', methods=['get', 'post'])
@render("index.html")
async def get_cat_help(service: CatService = Provide()):
    return service.list_cat()


@cat_router.get('/html/outside')
async def get_outside(request, service: CatService = Provide()):
    return render_template("index.html", request=request, context=service.list_cat())
