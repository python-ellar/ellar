from ellar.auth import IIdentityProvider
from ellar.common import Module
from ellar.di import ProviderConfig

from .controllers import ArticleController, MoviesControllers
from .identity_setup import IdentityProvider


@Module(
    controllers=(ArticleController, MoviesControllers),
    providers=[ProviderConfig(IIdentityProvider, use_class=IdentityProvider)],
)
class AppModule:
    pass
