"""
@Module(
    controllers=[MyController],
    providers=[
        YourService,
        ProviderConfig(IService, use_class=AService),
        ProviderConfig(IFoo, use_value=FooService()),
    ],
    routers=(routerA, routerB)
    statics='statics',
    template='template_folder',
    # base_directory -> default is the `auth` folder
)
class MyModule(ModuleBase):
    def register_providers(self, container: Container) -> None:
        # for more complicated provider registrations
        pass

"""
from ellar.common import Module
from ellar.core import ModuleBase
from ellar.di import Container

from .controllers import AuthController
from .services import AuthService


@Module(
    controllers=[AuthController],
    providers=[AuthService],
    routers=[],
)
class AuthModule(ModuleBase):
    """
    Auth Module
    """

    def register_providers(self, container: Container) -> None:
        """for more complicated provider registrations, use container.register_instance(...)"""
