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

from ellar.common import GlobalGuard, Module
from ellar.core import ForwardRefModule, ModuleBase
from ellar.core import LazyModuleImport as lazyLoad
from ellar.di import ProviderConfig
from ellar_jwt import JWTModule

from .controllers import AuthController
from .guards import AuthGuard
from .services import AuthService


@Module(
    modules=[
        lazyLoad("auth_project.users.module:UsersModule"),
        ForwardRefModule(JWTModule),
    ],
    controllers=[AuthController],
    providers=[
        AuthService,
        ProviderConfig(GlobalGuard, use_class=AuthGuard, core=True),
    ],
)
class AuthModule(ModuleBase):
    """
    Auth Module
    """
