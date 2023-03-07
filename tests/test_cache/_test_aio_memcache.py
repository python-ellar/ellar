# from time import sleep
#
# import pytest
#
# from ellar.cache.backends.aio_cache import AioMemCacheBackend
# from ellar.cache.model import CacheKeyWarning
#
# from .redis_mock import MockAsyncMemCacheClient
#
#
# class AioMemCacheBackendMock(AioMemCacheBackend):
#     MEMCACHE_CLIENT = MockAsyncMemCacheClient
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._client_options.update(time_lookup="exptime")
#
#
# @pytest.mark.asyncio
# async def test_aio_memcache_backend() -> None:
#     backend = AioMemCacheBackendMock(host="localhost", port=11211, pool_size=4)
#     await backend.set_async("test", "Wanaka", 1)
#     value = await backend.get_async("test")
#     assert value == "Wanaka"
#     sleep(1.1)
#     value = await backend.get_async("test")
#     assert not value
#
#
# class TestAioMemCacheBackend:
#     def setup(self):
#         self.backend = AioMemCacheBackendMock(host="localhost", port=11211, pool_size=4)
#
#     def test_set(self):
#         assert self.backend.set("test", "1", 1)
#         value = self.backend.get("test")
#         assert value == "1"
#
#     def test_has_key(self):
#         assert not self.backend.has_key("test-has-key")
#         assert self.backend.set("test-has-key", "1", 1)
#         assert self.backend.has_key("test-has-key")
#
#     def test_delete(self):
#         assert not self.backend.delete("test-delete")
#         assert self.backend.set("test-delete", "1", 1)
#         assert self.backend.delete("test-delete")
#
#     def test_touch(self):
#         assert not self.backend.touch("test-touch")
#         assert self.backend.set("test-touch", "1", 0.1)
#         assert self.backend.touch("test-touch", 30)
#         sleep(0.22)
#         assert self.backend.get("test-touch") == "1"
#
#     def test_invalid_key_length(self):
#         # memcached limits key length to 250.
#         key = ("a" * 250) + "清"
#         expected_warning = (
#             "Cache key will cause errors if used with memcached: "
#             "%r (longer than %s)" % (key, self.backend.MEMCACHE_MAX_KEY_LENGTH)
#         )
#         with pytest.warns(CacheKeyWarning) as wa:
#             self.backend.set(key, "value")
#         assert str(wa.list[0].message) == str(CacheKeyWarning(expected_warning))
#
#
# class TestAioMemCacheBackendAsync:
#     def setup(self):
#         self.backend = AioMemCacheBackendMock(host="localhost", port=11211, pool_size=4)
#
#     @pytest.mark.asyncio
#     async def test_set_async(
#         self,
#     ):
#         assert await self.backend.set_async("test", "1", 1)
#         value = await self.backend.get_async("test")
#         assert value == "1"
#
#     @pytest.mark.asyncio
#     async def test_has_key_async(self):
#         assert not await self.backend.has_key_async("test-has-key")
#         assert await self.backend.set_async("test-has-key", "1", 1)
#         assert await self.backend.has_key_async("test-has-key")
#
#     @pytest.mark.asyncio
#     async def test_delete_async(
#         self,
#     ):
#         assert not await self.backend.delete_async("test-delete")
#         assert await self.backend.set_async("test-delete", "1", 0.1)
#         assert await self.backend.delete_async("test-delete")
#
#     @pytest.mark.asyncio
#     async def test_touch_async(self):
#         assert not await self.backend.touch_async("test-touch")
#         assert await self.backend.set_async("test-touch", "1", 0.1)
#         assert await self.backend.touch_async("test-touch", 30)
#         sleep(0.22)
#         assert await self.backend.get_async("test-touch") == "1"
