from typing import List
from dataclasses import dataclass

from catapp.application.cats.services import CatService
from architek.core.response.serializer import DataClassSerializer
from architek.core.routing import ModuleRouter
from architek.common import provide, req, Render
from architek.core.templating import render_template

cat_router = ModuleRouter("/cats-router", tag='Testing')


@dataclass
class CatObject(DataClassSerializer):
    name: str


@cat_router.Get(response={200: List[CatObject]})
async def get_cats(request=req(), service: CatService = provide()):
    return service.list_cat()


@cat_router.HttpRoute('/html', methods=['get', 'post'])
@Render("index.html")
async def get_cat_help(service: CatService = provide()):
    return service.list_cat()


@cat_router.Get('/html/outside')
async def get_outside(request, service: CatService = provide()):
    return render_template("index.html", request=request, context=service.list_cat())
