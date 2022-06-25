from ellar.common import Module

from ..application.cats.module import CatModule


@Module(
    modules=(CatModule, )
)
class AppModuleTest:
    pass
