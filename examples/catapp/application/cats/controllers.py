from ellar.common import Controller, Ctx, delete, get, put, render, version

from .services import CatService


@Controller
class CatController:
    def __init__(self, cat_service: CatService) -> None:
        self.cat_service = cat_service

    @get("/create")
    async def create_cat(self):
        return self.cat_service.create_cat()

    @put("/{cat_id:int}")
    async def update_cat(self, cat_id: int):
        return self.cat_service.update_cat(cat_id)

    @delete("/{cat_id:int}")
    async def deleted_cat(self, cat_id: int):
        return self.cat_service.deleted_cat(cat_id)

    @get("/")
    @render()
    async def list(self, ctx=Ctx()):
        return self.cat_service.list_cat()

    @get("/create", name='v2_create')
    @version('v2')
    async def create_cat_v2(self):
        return self.cat_service.create_cat()
