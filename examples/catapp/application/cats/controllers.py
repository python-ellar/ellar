from catapp.application.cats.services import CatService
from ellar.common import Controller, Get, Put, Post, Delete, version, Render, Ctx


@Controller
class CatController:
    def __init__(self, cat_service: CatService) -> None:
        self.cat_service = cat_service

    @Get("/create")
    async def create_cat(self):
        return self.cat_service.create_cat()

    @Put("/{cat_id:int}")
    async def update_cat(self, cat_id: int):
        return self.cat_service.update_cat(cat_id)

    @Delete("/{cat_id:int}")
    async def deleted_cat(self, cat_id: int):
        return self.cat_service.deleted_cat(cat_id)

    @Get("/")
    @Render()
    async def list(self, ctx=Ctx()):
        return self.cat_service.list_cat()

    @Get("/create", name='v2_create')
    @version('v2')
    async def create_cat_v2(self):
        return self.cat_service.create_cat()
