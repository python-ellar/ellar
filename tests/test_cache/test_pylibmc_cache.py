from time import sleep

import pytest

from ellar.cache.backends.pylib_cache import PyLibMCCacheBackend
from ellar.cache.backends.pymem_cache import PyMemcacheCacheBackend

from .pylib_mock import MockClient


class PyLibMCCacheBackendMock(PyLibMCCacheBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_client_class = MockClient


@pytest.mark.asyncio
async def test_simple_cache_backend() -> None:
    backend = PyLibMCCacheBackendMock(
        server=["127.0.0.1:11211"],
        options=dict(binary=True, behaviors={"tcp_nodelay": True, "ketama": True}),
    )
    assert backend._cache_client.kwargs == dict(
        binary=True, behaviors={"tcp_nodelay": True, "ketama": True}
    )
    await backend.set_async("test", "Wanaka", 1)
    value = await backend.get_async("test")
    assert value == "Wanaka"
    sleep(1.1)
    value = await backend.get_async("test")
    assert not value


class TestPyLibMCCacheBackend:
    def setup(self):
        self.backend = PyLibMCCacheBackendMock(server=["127.0.0.1:11211"])

    def test_set(self):
        assert self.backend.set("test", "1", 1)
        value = self.backend.get("test")
        assert value == "1"

    def test_has_key(self):
        assert not self.backend.has_key("test-has-key")
        assert self.backend.set("test-has-key", "1", 1)
        assert self.backend.has_key("test-has-key")

    def test_delete(self):
        assert not self.backend.delete("test-delete")
        assert self.backend.set("test-delete", "1", 1)
        assert self.backend.delete("test-delete")

    def test_touch(self):
        assert not self.backend.touch("test-touch")
        assert self.backend.set("test-touch", "1", 0.1)
        assert self.backend.touch("test-touch", 30)
        sleep(0.22)
        assert self.backend.get("test-touch") == "1"
        assert self.backend.close() is None


class TestPyLibMCCacheBackendAsync:
    def setup(self):
        self.backend = PyLibMCCacheBackendMock(server=["127.0.0.1:11211"])

    async def test_set_async(self, anyio_backend):
        assert await self.backend.set_async("test", "1", 1)
        value = await self.backend.get_async("test")
        assert value == "1"

    async def test_has_key_async(self, anyio_backend):
        assert not await self.backend.has_key_async("test-has-key")
        assert await self.backend.set_async("test-has-key", "1", 1)
        assert await self.backend.has_key_async("test-has-key")

    async def test_delete_async(self, anyio_backend):
        assert not await self.backend.delete_async("test-delete")
        assert await self.backend.set_async("test-delete", "1", 1)
        assert await self.backend.delete_async("test-delete")

    async def test_touch_async(self, anyio_backend):
        assert not await self.backend.touch_async("test-touch")
        assert await self.backend.set_async("test-touch", "1", 1)
        assert await self.backend.touch_async("test-touch", 30)
        sleep(0.22)
        assert await self.backend.get_async("test-touch") == "1"
        assert await self.backend.close_async() is None


class TestPyMemCacheBackend:
    def test_init_pymemcache_backend(self):
        backend = PyMemcacheCacheBackend(server=["127.0.0.1:11211"])
        backend._options.pop("serde")
        assert backend._options == {
            "allow_unicode_keys": True,
            "default_noreply": False,
        }
