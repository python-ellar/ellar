from time import sleep

from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.cache.service import CacheService


class TestCacheService:
    def setup(self):
        self.cache_service = CacheService(dict(default=LocalMemCacheBackend()))

    def test_set(self):
        assert self.cache_service.set("test", "1", 0.1)
        value = self.cache_service.get("test")
        assert value == "1"

    def test_has_key(self):
        assert not self.cache_service.has_key("test-has-key")
        assert self.cache_service.set("test-has-key", "1", 0.1)
        assert self.cache_service.has_key("test-has-key")

    def test_delete(self):
        assert not self.cache_service.delete("test-delete")
        assert self.cache_service.set("test-delete", "1", 0.1)
        assert self.cache_service.delete("test-delete")

    def test_touch(self):
        assert not self.cache_service.touch("test-touch")
        assert self.cache_service.set("test-touch", "1", 0.1)
        assert self.cache_service.touch("test-touch", 30)
        sleep(0.22)
        assert self.cache_service.get("test-touch") == "1"


class TestCacheServiceAsync:
    def setup(self):
        self.cache_service = CacheService(dict(default=LocalMemCacheBackend()))

    async def test_set_async(self, anyio_backend):
        assert await self.cache_service.set_async("test", "1", 0.1)
        value = await self.cache_service.get_async("test")
        assert value == "1"

    async def test_has_key_async(self, anyio_backend):
        assert not await self.cache_service.has_key_async("test-has-key")
        assert await self.cache_service.set_async("test-has-key", "1", 0.1)
        assert await self.cache_service.has_key_async("test-has-key")

    async def test_delete_async(self, anyio_backend):
        assert not await self.cache_service.delete_async("test-delete")
        assert await self.cache_service.set_async("test-delete", "1", 0.1)
        assert await self.cache_service.delete_async("test-delete")

    async def test_touch_async(self, anyio_backend):
        assert not await self.cache_service.touch_async("test-touch")
        assert await self.cache_service.set_async("test-touch", "1", 0.1)
        assert await self.cache_service.touch_async("test-touch", 30)
        sleep(0.22)
        assert await self.cache_service.get_async("test-touch") == "1"
