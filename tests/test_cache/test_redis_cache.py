from time import sleep

import pytest

from ellar.cache.backends.redis import RedisCacheBackend

from .redis_mock import MockRedisClient


class RedisCacheBackendMock(RedisCacheBackend):
    def _get_client(self, *, write: bool = False) -> MockRedisClient:
        pool = self._get_connection_pool(write)
        return MockRedisClient(connection_pool=pool)


@pytest.mark.asyncio
async def test_redis_backend() -> None:
    backend = RedisCacheBackendMock(servers=["redis://localhost:6379/0"])
    await backend.set_async("test", "Wanaka", 1)
    value = await backend.get_async("test")
    assert value == "Wanaka"
    sleep(1.1)
    value = await backend.get_async("test")
    assert not value


class TestRedisCacheBackend:
    def setup(self):
        self.backend = RedisCacheBackendMock(servers=["redis://localhost:6379/0"])

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


class TestRedisCacheBackendAsync:
    def setup(self):
        self.backend = RedisCacheBackendMock(servers=["redis://localhost:6379/0"])

    @pytest.mark.asyncio
    async def test_set_async(
        self,
    ):
        assert await self.backend.set_async("test-async", "1", 1)
        value = await self.backend.get_async("test")
        assert value == "1"

    @pytest.mark.asyncio
    async def test_has_key_async(
        self,
    ):
        assert not await self.backend.has_key_async("test-has-key-async")
        assert await self.backend.set_async("test-has-key", "1", 1)
        assert await self.backend.has_key_async("test-has-key")

    @pytest.mark.asyncio
    async def test_delete_async(
        self,
    ):
        assert not await self.backend.delete_async("test-delete-async")
        assert await self.backend.set_async("test-delete", "1", 0.1)
        assert await self.backend.delete_async("test-delete")

    @pytest.mark.asyncio
    async def test_touch_async(
        self,
    ):
        assert not await self.backend.touch_async("test-touch-async")
        assert await self.backend.set_async("test-touch", "1", 0.1)
        assert await self.backend.touch_async("test-touch", 30)
        sleep(0.22)
        assert await self.backend.get_async("test-touch") == "1"
