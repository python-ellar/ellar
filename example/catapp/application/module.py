from app_module_test.application.cats.module import CatModule
from architek.module import ApplicationModule


@ApplicationModule(
    modules=(CatModule, )
)
class AppModuleTest:
    pass
