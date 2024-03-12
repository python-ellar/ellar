from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.cache.module import CacheModule
from ellar.common import (
    IExecutionContext,
    JSONResponse,
    Module,
    Response,
    exception_handler,
)
from ellar.core import ModuleBase
from ellar.samples.modules import HomeModule

from .controller import CacheControllerTest

# Using CacheModule Setup
CACHE_MODULE = CacheModule.setup(
    default=LocalMemCacheBackend(ttl=300, key_prefix="local", version=1),
    secondary=LocalMemCacheBackend(ttl=500, key_prefix="secondary", version=2),
)
# Using CacheModule Register Setup
# CACHE_MODULE = CacheModule.register_setup()

# And with this pattern Cache config has to be defined in config.py
# For example:
# class DevelopmentConfig(ConfigDefaultTypesMixin):
#     CACHES = {
#         'default': LocalMemCacheBackend(ttl=300, key_prefix='local', version=1)
#     }
# See Docs: https://python-ellar.github.io/ellar/techniques/caching/


@Module(modules=[HomeModule, CACHE_MODULE], controllers=[CacheControllerTest])
class ApplicationModule(ModuleBase):
    @exception_handler(404)
    def exception_404_handler(cls, ctx: IExecutionContext, exc: Exception) -> Response:
        return JSONResponse({"detail": "Resource not found."}, status_code=404)
