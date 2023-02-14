from time import sleep

from ellar.cache.backends.simple_cache import SimpleCacheBackend


async def test_simple_cache_backend(anyio_backend: str) -> None:
    backend = SimpleCacheBackend()
    await backend.set("test", "1", 0.1)  # type: ignore
    value = await backend.get("test")
    assert value
    sleep(0.2)
    value = await backend.get("test")
    assert not value


async def test_simple_cache_backend_with_init_params(anyio_backend: str) -> None:
    backend = SimpleCacheBackend(key_prefix="ellar", timeout=300, version=2)
    await backend.set("test", "1", 20)  # type: ignore
    key = backend.make_key("test")
    assert backend._cache[key]
    assert isinstance(backend._cache[key], bytes)


async def test_simple_cache_backend_has_key_and_delete(anyio_backend: str) -> None:
    backend = SimpleCacheBackend()
    await backend.set_async("test", "1", 2000)  # type: ignore
    assert await backend.has_key_async("test")
    assert await backend.delete_async("test") is True
    assert not await backend.has_key_async("test")


def test_simple_cache_backend_has_key_and_delete_sync(anyio_backend: str) -> None:
    backend = SimpleCacheBackend()
    backend.set("test", "1", 2000)  # type: ignore
    assert backend.get("test") == "1"
    assert backend.has_key("test")
    assert backend.delete("test") is True
    assert not backend.has_key("test")
