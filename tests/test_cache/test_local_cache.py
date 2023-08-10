from time import sleep

import pytest
from ellar.cache.backends.local_cache import LocalMemCacheBackend


class TestLocalMemCacheBackend:
    def setup_method(self):
        self.backend = LocalMemCacheBackend()

    def test_set(self):
        assert self.backend.set("test", "1", 0.1)
        value = self.backend.get("test")
        assert value == "1"

    def test_has_key(self):
        assert not self.backend.has_key("test-has-key")
        assert self.backend.set("test-has-key", "1", 0.1)
        assert self.backend.has_key("test-has-key")

    def test_delete(self):
        assert not self.backend.delete("test-delete")
        assert self.backend.set("test-delete", "1", 0.1)
        assert self.backend.delete("test-delete")

    def test_touch(self):
        assert not self.backend.touch("test-touch")
        assert self.backend.set("test-touch", "1", 0.1)
        assert self.backend.touch("test-touch", 30)
        sleep(0.22)
        assert self.backend.get("test-touch") == "1"

    def test_cache_zero_timeout_expires_immediately(self):
        assert self.backend.set("test-touch", 1, 0)
        assert self.backend.get("test-touch") is None

    def test_incr(self):
        self.backend.set("test-incr-backend", 0, version="1", ttl=0.1)
        self.backend.incr("test-incr-backend", version="1")
        assert self.backend.get("test-incr-backend", version="1") == 1
        self.backend.incr("test-incr-backend", 2, version="1")
        self.backend.incr("test-incr-backend", 3, version="1")
        assert self.backend.get("test-incr-backend") == 6

    def test_decr(self):
        self.backend.set("test-decr-backend", 2, version="1", ttl=0.1)
        self.backend.decr("test-decr-backend", version="1")
        assert self.backend.get("test-decr-backend", version="1") == 1

        self.backend.decr("test-decr-backend", 2, version="1")
        self.backend.decr("test-decr-backend", 3, version="1")
        assert self.backend.get("test-decr-backend") == 0


class TestLocalMemCacheBackendAsync:
    def setup_method(self):
        self.backend = LocalMemCacheBackend()

    async def test_set_async(self, anyio_backend):
        assert await self.backend.set_async("test", "1", 0.1)
        value = await self.backend.get_async("test")
        assert value == "1"

    async def test_has_key_async(self, anyio_backend):
        assert not await self.backend.has_key_async("test-has-key")
        assert await self.backend.set_async("test-has-key", "1", 0.1)
        assert await self.backend.has_key_async("test-has-key")

    async def test_delete_async(self, anyio_backend):
        assert not await self.backend.delete_async("test-delete")
        assert await self.backend.set_async("test-delete", "1", 0.1)
        assert await self.backend.delete_async("test-delete")

    async def test_touch_async(self, anyio_backend):
        assert not await self.backend.touch_async("test-touch")
        assert await self.backend.set_async("test-touch", "1", 0.1)
        assert await self.backend.touch_async("test-touch", 30)
        sleep(0.22)
        assert await self.backend.get_async("test-touch") == "1"

    async def test_simple_cache_backend_with_init_params(
        self, anyio_backend: str
    ) -> None:
        backend = LocalMemCacheBackend(key_prefix="ellar", ttl=300, version=2)
        await backend.set_async("test", "2", 20)  # type: ignore
        key = backend.make_key("test")
        assert backend._cache[key]
        assert isinstance(backend._cache[key], bytes)

    async def test_incr_async(self, anyio_backend):
        await self.backend.set_async("test-incr-async-backend", 0, version="1", ttl=0.1)
        await self.backend.incr_async("test-incr-async-backend", version="1")
        assert await self.backend.get_async("test-incr-async-backend", version="1") == 1
        await self.backend.incr_async("test-incr-async-backend", 2, version="1")
        await self.backend.incr_async("test-incr-async-backend", 3, version="1")
        assert await self.backend.get_async("test-incr-async-backend") == 6

        with pytest.raises(ValueError):
            await self.backend.set_async("test-incr-async-backend", 0, ttl=0)
            await self.backend.incr_async("test-incr-async-backend")

    async def test_decr_async(self, anyio_backend):
        await self.backend.set_async("test-decr-async-backend", 2, version="1", ttl=0.2)
        await self.backend.decr_async("test-decr-async-backend", version="1")
        assert await self.backend.get_async("test-decr-async-backend", version="1") == 1

        await self.backend.decr_async("test-decr-async-backend", 2, version="1")
        await self.backend.decr_async("test-decr-async-backend", 3, version="1")
        assert await self.backend.get_async("test-decr-async-backend") == 0

        with pytest.raises(ValueError):
            await self.backend.set_async("test-decr-async-backend", 2, ttl=0)
            await self.backend.decr_async("test-decr-async-backend")
