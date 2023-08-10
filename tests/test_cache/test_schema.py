import pytest
from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.cache.schema import CacheModuleSchemaSetup


def test_invalid_cached_backend_config():
    with pytest.raises(ValueError, match="Expected BaseCacheBackend, received:"):
        CacheModuleSchemaSetup(CACHES={"default": type("whatever", (), {})})


def test_cache_backend_without_default_raise_exception():
    with pytest.raises(
        ValueError, match="CACHES configuration must have a 'default' key"
    ):
        CacheModuleSchemaSetup(CACHES={"local": LocalMemCacheBackend()})
