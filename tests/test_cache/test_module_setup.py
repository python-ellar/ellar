from ellar.cache import CacheModule, ICacheService
from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.core import TestClientFactory


def test_cache_module_setup_works():
    tm = TestClientFactory.create_test_module(
        modules=[
            CacheModule.setup(
                default=LocalMemCacheBackend(),
                local=LocalMemCacheBackend(version=2, ttl=400),
            )
        ]
    )

    cache_service = tm.app.injector.get(ICacheService)
    assert cache_service
    local = cache_service.get_backend("local")

    assert local._version == 2
    assert local._default_ttl == 400
