from catapp.application.cats.module import CatModule
from ellar.common import ApplicationModule


@ApplicationModule(
    modules=(CatModule, )
)
class AppModuleTest:
    pass
