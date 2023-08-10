from time import sleep

import pytest
from ellar.cache.backends.local_cache import LocalMemCacheBackend
from ellar.cache.service import CacheService, InvalidCacheBackendKeyException


class TestCacheService:
    def setup_method(self):
        self.cache_service = CacheService({"default": LocalMemCacheBackend()})

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

    def test_incr(self):
        self.cache_service.set("test-incr", 0, version="1", ttl=0.1)
        self.cache_service.incr("test-incr", version="1")
        assert self.cache_service.get("test-incr", version="1") == 1
        self.cache_service.incr("test-incr", 2, version="1")
        self.cache_service.incr("test-incr", 3, version="1")
        assert self.cache_service.get("test-incr") == 6

    def test_decr(self):
        self.cache_service.set("test-decr", 2, version="1", ttl=0.1)
        self.cache_service.decr("test-decr", version="1")
        assert self.cache_service.get("test-decr", version="1") == 1

        self.cache_service.decr("test-decr", 2, version="1")
        self.cache_service.decr("test-decr", 3, version="1")
        assert self.cache_service.get("test-decr") == 0

    def test_get_backend(self):
        backend_default = self.cache_service.get_backend("default")
        assert isinstance(backend_default, LocalMemCacheBackend)

        backend = self.cache_service.get_backend()  # return default
        assert isinstance(backend, LocalMemCacheBackend) and backend == backend_default

        with pytest.raises(InvalidCacheBackendKeyException):
            self.cache_service.get_backend("what_doesnot_exist_will_raise_exception")


class TestCacheServiceAsync:
    def setup_method(self):
        self.cache_service = CacheService({"default": LocalMemCacheBackend()})

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

    async def test_incr_async(self, anyio_backend):
        await self.cache_service.set_async("test-incr-async", 0, version="1", ttl=0.1)
        await self.cache_service.incr_async("test-incr-async", version="1")
        assert await self.cache_service.get_async("test-incr-async", version="1") == 1
        await self.cache_service.incr_async("test-incr-async", 2, version="1")
        await self.cache_service.incr_async("test-incr-async", 3, version="1")
        assert await self.cache_service.get_async("test-incr-async") == 6

    async def test_decr_async(self, anyio_backend):
        await self.cache_service.set_async("test-decr-async", 2, version="1", ttl=0.2)
        await self.cache_service.decr_async("test-decr-async", version="1")
        assert await self.cache_service.get_async("test-decr-async", version="1") == 1

        await self.cache_service.decr_async("test-decr-async", 2, version="1")
        await self.cache_service.decr_async("test-decr-async", 3, version="1")
        assert await self.cache_service.get_async("test-decr-async") == 0
