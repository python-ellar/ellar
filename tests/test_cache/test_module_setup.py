from ellar.cache import CacheModule, ICacheService
from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.testing import Test


def test_cache_module_setup_works():
    tm = Test.create_test_module(
        modules=[
            CacheModule.setup(
                default=LocalMemCacheBackend(),
                local=LocalMemCacheBackend(version=2, ttl=400),
            )
        ]
    )

    cache_service = tm.get(ICacheService)
    assert cache_service
    local = cache_service.get_backend("local")

    assert local._version == 2
    assert local._default_ttl == 400
