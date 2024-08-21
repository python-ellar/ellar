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

from ellar.app import use_authentication_schemes
from ellar.common import Module
from ellar.core import LazyModuleImport as lazyLoad
from ellar.core import ModuleBase
from ellar_jwt import JWTModule

from .auth_scheme import JWTAuthentication
from .controllers import AuthController
from .services import AuthService

# Register JWTAuthentication as an authentication scheme
use_authentication_schemes(JWTAuthentication)


@Module(
    modules=[
        lazyLoad("auth_project_with_handler.users.module:UsersModule"),
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
