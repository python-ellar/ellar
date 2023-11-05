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
from datetime import timedelta

from ellar.common import Module
from ellar.core import ModuleBase
from ellar_jwt import JWTModule

from ..users.module import UsersModule
from .controllers import AuthController
from .services import AuthService


@Module(
    modules=[
        UsersModule,
        JWTModule.setup(
            signing_secret_key="my_poor_secret_key_lol", lifetime=timedelta(minutes=5)
        ),
    ],
    controllers=[AuthController],
    providers=[AuthService],
)
class AuthModule(ModuleBase):
    """
    Auth Module
    """
