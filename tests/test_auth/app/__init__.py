from ellar.auth import IIdentitySchemeProvider
from ellar.common import Module
from ellar.di import ProviderConfig

from .controllers import ArticleController, MoviesControllers
from .identity_setup import IdentitySchemeProvider


@Module(
    controllers=(ArticleController, MoviesControllers),
    providers=[
        ProviderConfig(IIdentitySchemeProvider, use_class=IdentitySchemeProvider)
    ],
)
class AppModule:
    pass
