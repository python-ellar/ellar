from time import sleep
from unittest.mock import patch

import pytest
from ellar.cache.backends.pylib_cache import PyLibMCCacheBackend
from ellar.cache.backends.pymem_cache import PyMemcacheCacheBackend
from ellar.cache.model import CacheKeyWarning

from .pylib_mock import MockClient, MockSetFailureClient


class PyLibMCCacheBackendMock(PyLibMCCacheBackend):
    MEMCACHE_CLIENT = MockClient


@pytest.mark.asyncio
async def test_simple_cache_backend() -> None:
    backend = PyLibMCCacheBackendMock(
        servers=["127.0.0.1:11211"],
        options={"binary": True, "behaviors": {"tcp_nodelay": True, "ketama": True}},
    )
    assert backend._cache_client.kwargs == {
        "binary": True,
        "behaviors": {"tcp_nodelay": True, "ketama": True},
    }
    await backend.set_async("test", "Wanaka", 1)
    value = await backend.get_async("test")
    assert value == "Wanaka"
    sleep(1.1)
    value = await backend.get_async("test")
    assert not value


class TestPyLibMCCacheBackend:
    def setup_method(self):
        self.backend = PyLibMCCacheBackendMock(servers=["127.0.0.1:11211"])

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

    def test_incr(self):
        self.backend.set("test-incr-sync", 0, version="1", ttl=1)
        self.backend.incr("test-incr-sync", version="1")
        assert self.backend.get("test-incr-sync", version="1") == 1

        self.backend.incr("test-incr-sync", 2, version="1")
        self.backend.incr("test-incr-sync", 3, version="1")
        assert self.backend.get("test-incr-sync") == 6

    def test_decr(self):
        self.backend.set("test-decr-sync", 2, version="1", ttl=1)
        self.backend.decr("test-decr-sync", version="1")
        assert self.backend.get("test-decr-sync", version="1") == 1

        self.backend.decr("test-decr-sync", 2, version="1")
        self.backend.decr("test-decr-sync", 3, version="1")
        assert self.backend.get("test-decr-sync") == 0

    def test_clear(self):
        assert self.backend.set("test-touch", "1", 0.1)
        self.backend.clear()
        assert self.backend.get("test-touch") is None

    def test_failed_cache_set_deletes_existing_data(self):
        class DemoPyLibMemCacheBackend(PyLibMCCacheBackend):
            MEMCACHE_CLIENT = MockSetFailureClient

        self.backend = DemoPyLibMemCacheBackend(servers=["127.0.0.1:11211"])
        assert self.backend.set("test-set-failed", "1", 5) is False
        assert self.backend.get("test-set-failed") is None

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

    def test_invalid_key_characters(self):
        # memcached doesn't allow whitespace or control characters in keys.
        key = "key with spaces and 清"
        expected_warning = (
            "Cache key contains characters that will cause errors if used with memcached: %r"
            % (key,)
        )
        with pytest.warns(CacheKeyWarning) as wa:
            self.backend.set(key, "value")
        assert str(wa.list[0].message) == str(CacheKeyWarning(expected_warning))


class TestPyLibMCCacheBackendAsync:
    def setup_method(self):
        self.backend = PyLibMCCacheBackendMock(servers=["127.0.0.1:11211"])

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

    async def test_clear(self, anyio_backend):
        assert self.backend.set_async("test-touch", "1", 0.1)
        await self.backend.clear_async()
        assert await self.backend.get_async("test-touch") is None

    async def test_incr_async(self, anyio_backend):
        await self.backend.set_async(
            f"test-incr-async-{anyio_backend}", 0, version="1", ttl=1
        )
        await self.backend.incr_async(f"test-incr-async-{anyio_backend}", version="1")
        assert (
            await self.backend.get_async(
                f"test-incr-async-{anyio_backend}", version="1"
            )
            == 1
        )
        await self.backend.incr_async(
            f"test-incr-async-{anyio_backend}", 2, version="1"
        )
        await self.backend.incr_async(
            f"test-incr-async-{anyio_backend}", 3, version="1"
        )
        assert await self.backend.get_async(f"test-incr-async-{anyio_backend}") == 6

    async def test_decr_async(self, anyio_backend):
        await self.backend.set_async("test-decr-async-pylib", 2, version="1", ttl=1)
        await self.backend.decr_async("test-decr-async-pylib", version="1")
        assert await self.backend.get_async("test-decr-async-pylib", version="1") == 1

        await self.backend.decr_async("test-decr-async-pylib", 2, version="1")
        await self.backend.decr_async("test-decr-async-pylib", 3, version="1")
        assert await self.backend.get_async("test-decr-async-pylib") == 0


class TestPyMemCacheBackend:
    def test_init_pymemcache_backend(self):
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211"])
        backend._options.pop("serde")
        assert backend._options == {
            "allow_unicode_keys": True,
            "default_noreply": False,
        }
        assert backend.close() is None

    def test_different_connection_setup(self):
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211", "172.10.169.53"])
        assert len(backend._cache_client.clients) == 2
        assert ["127.0.0.1:11211", "172.10.169.53:11211"] == list(
            backend._cache_client.clients.keys()
        )

    @patch("pymemcache.HashClient.flush_all")
    async def test_clear_async(self, mock_flush_all, anyio_backend):
        assert mock_flush_all.called is False
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211"])
        await backend.clear_async()
        assert mock_flush_all.called is True

    @patch("pymemcache.Client.close")
    async def test_close_async(self, mock_disconnect_all, anyio_backend):
        assert mock_disconnect_all.called is False
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211"])
        await backend.close_async()
        assert mock_disconnect_all.called is True

    @patch("pymemcache.HashClient.flush_all")
    def test_clear(self, mock_flush_all):
        assert mock_flush_all.called is False
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211"])
        backend.clear()
        assert mock_flush_all.called is True

    @patch("pymemcache.Client.close")
    def test_close(self, mock_disconnect_all):
        assert mock_disconnect_all.called is False
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211"])
        backend.close()
        assert mock_disconnect_all.called is True

    @patch("pymemcache.HashClient.set")
    def test_invalid_key_length(self, mock_set):
        # memcached limits key length to 250.
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211"])
        key = ("a" * 250) + "清"
        expected_warning = (
            "Cache key will cause errors if used with memcached: "
            "%r (longer than %s)" % (key, backend.MEMCACHE_MAX_KEY_LENGTH)
        )
        with pytest.warns(CacheKeyWarning) as wa:
            backend.set(key, "value")
        assert str(wa.list[0].message) == str(CacheKeyWarning(expected_warning))

    @patch("pymemcache.HashClient.set")
    def test_invalid_key_characters(self, mock_set):
        backend = PyMemcacheCacheBackend(servers=["127.0.0.1:11211"])
        # memcached doesn't allow whitespace or control characters in keys.
        key = "key with spaces and 清"
        expected_warning = (
            "Cache key contains characters that will cause errors if used with memcached: %r"
            % (key,)
        )
        with pytest.warns(CacheKeyWarning) as wa:
            backend.set(key, "value")
        assert str(wa.list[0].message) == str(CacheKeyWarning(expected_warning))
