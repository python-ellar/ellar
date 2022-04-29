from ellar.core.modules import ModuleBase

from catapp.application.cats.controllers import CatController
from catapp.application.cats.routers import cat_router
from catapp.application.cats.services import CatService, AnotherService
from ellar.common import Module


@Module(
    name='cats',
    controllers=(CatController,),
    routers=(cat_router, ),
    providers=(CatService, AnotherService),
    template_folder='views',
    static_folder='statics'
)
class CatModule(ModuleBase):
    pass
