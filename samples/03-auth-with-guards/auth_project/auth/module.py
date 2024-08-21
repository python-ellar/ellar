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

from ellar.app import use_global_guards
from ellar.common import Module
from ellar.core import ForwardRefModule, ModuleBase
from ellar.core import LazyModuleImport as lazyLoad
from ellar_jwt import JWTModule

from .controllers import AuthController
from .guards import AuthGuard
from .services import AuthService

## Sets AuthGuard as a GLOBAL GUARD in application config.
use_global_guards(AuthGuard)


@Module(
    modules=[
        lazyLoad("auth_project.users.module:UsersModule"),
        ForwardRefModule(JWTModule),
    ],
    controllers=[AuthController],
    providers=[
        AuthService,
    ],
)
class AuthModule(ModuleBase):
    """
    Auth Module
    """
