from catapp.application.cats.module import CatModule
from architek.common import ApplicationModule


@ApplicationModule(
    modules=(CatModule, )
)
class AppModuleTest:
    pass
