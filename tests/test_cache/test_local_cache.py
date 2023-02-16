from time import sleep

from ellar.cache.backends.local_cache import LocalMemCacheBackend


class TestLocalMemCacheBackend:
    def setup(self):
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


class TestLocalMemCacheBackendAsync:
    def setup(self):
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
        backend = LocalMemCacheBackend(key_prefix="ellar", timeout=300, version=2)
        await backend.set_async("test", "2", 20)  # type: ignore
        key = backend.make_key("test")
        assert backend._cache[key]
        assert isinstance(backend._cache[key], bytes)
