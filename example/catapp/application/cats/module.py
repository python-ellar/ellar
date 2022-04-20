from architek.core.modules import ModuleBase

from app_module_test.application.cats.controllers import CatController
from app_module_test.application.cats.routers import cat_router
from app_module_test.application.cats.services import CatService, AnotherService
from architek.common import Module


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
