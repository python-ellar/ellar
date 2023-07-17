from ellar.common import Module

from .auth import SimpleHeaderAuthHandler
from .controllers import ArticleController, MoviesControllers

__all__ = ["AppModule", "SimpleHeaderAuthHandler"]


@Module(
    controllers=(ArticleController, MoviesControllers),
)
class AppModule:
    pass
