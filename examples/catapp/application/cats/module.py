from ellar.common import Module
from ellar.core.modules import ModuleBase

from .controllers import CatController
from .routers import cat_router
from .services import AnotherService, CatService


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
