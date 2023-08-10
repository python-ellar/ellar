from time import sleep

import pytest
from ellar.cache.backends.redis import RedisCacheBackend
from ellar.cache.model import CacheKeyWarning

from .redis_mock import MockRedisClient


class RedisCacheBackendMock(RedisCacheBackend):
    MEMCACHE_CLIENT = MockRedisClient


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
    def setup_method(self):
        self.backend = RedisCacheBackendMock(
            servers=[
                "redis://localhost:6379/0",
                "redis://localhost:6379/1",
                "redis://localhost:6379/2",
            ]
        )

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

    def test_incr_async(self):
        self.backend.set("test-incr", 0, ttl=1)
        self.backend.incr("test-incr")

        assert self.backend.get("test-incr") == 1
        self.backend.incr("test-incr", 2)

        self.backend.incr("test-incr", 3)
        assert self.backend.get("test-incr") == 6

    def test_decr_async(self):
        self.backend.set("test-decr", 2, ttl=1)
        self.backend.decr("test-decr")

        assert self.backend.get("test-decr") == 1
        self.backend.decr("test-decr", 2)

        self.backend.decr("test-decr", 3)
        assert self.backend.get("test-decr") == 0

    def test_pickling_int_values_is_skipped(self):
        assert self.backend.set("test-int-key", 1, 1)
        assert self.backend.get("test-int-key") == 1

    def test_invalid_key_length(self):
        # memcached limits key length to 250.
        key = ("a" * 250) + "清"
        expected_warning = (
            "Cache key will cause errors if used with memcached: "
            "%r (longer than %s)" % (key, self.backend.MEMCACHE_MAX_KEY_LENGTH)
        )
        with pytest.warns(CacheKeyWarning) as wa:
            self.backend.set(key, "value")
        assert str(wa.list[0].message) == str(CacheKeyWarning(expected_warning))


class TestRedisCacheBackendAsync:
    def setup_method(self):
        self.backend = RedisCacheBackendMock(
            servers=[
                "redis://localhost:6379/0",
                "redis://localhost:6379/1",
                "redis://localhost:6379/2",
            ]
        )

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

    @pytest.mark.asyncio
    async def test_incr_async(self):
        await self.backend.set_async("test-incr-async", 0, ttl=1)
        await self.backend.incr_async("test-incr-async")
        assert await self.backend.get_async("test-incr-async") == 1
        await self.backend.incr_async("test-incr-async", 2)
        await self.backend.incr_async("test-incr-async", 3)
        assert await self.backend.get_async("test-incr-async") == 6

    @pytest.mark.asyncio
    async def test_decr_async(self):
        await self.backend.set_async("test-decr-async", 2, ttl=1)
        await self.backend.decr_async("test-decr-async")
        assert await self.backend.get_async("test-decr-async") == 1

        await self.backend.decr_async("test-decr-async", 2)
        await self.backend.decr_async("test-decr-async", 3)
        assert await self.backend.get_async("test-decr-async") == 0

    @pytest.mark.asyncio
    async def test_zero_timeout_deletes_old_value_if_any(self):
        delete_called = False
        set_called = False

        class DemoCacheClient:
            def __init__(self, *args, **kwargs):
                pass

            async def delete(self, *args, **kwargs):
                nonlocal delete_called
                delete_called = True
                return True

            async def set(self, *args, **kwargs):
                nonlocal set_called
                set_called = True
                return True

        class DemoMemCachedBackend(RedisCacheBackend):
            MEMCACHE_CLIENT = DemoCacheClient

        backend = DemoMemCachedBackend(servers=["redis://localhost:6379/0"])
        await backend.set_async("zero", "value", ttl=0)
        assert set_called and delete_called
