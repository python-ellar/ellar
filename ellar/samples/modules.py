from ellar.common import Module

from ..core import ModuleBase
from .controllers.home import HomeController


@Module(controllers=[HomeController], static_folder="static")
class HomeModule(ModuleBase):
    pass
