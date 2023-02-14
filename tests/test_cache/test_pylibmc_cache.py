import pytest

from ellar.cache.backends.pylib_cache import PyLibMCCacheBackend


@pytest.mark.asyncio
async def test_simple_cache_backend() -> None:
    backend = PyLibMCCacheBackend(
        server=["127.0.0.1:11211"],
        options=dict(binary=True, behaviors={"tcp_nodelay": True, "ketama": True}),
    )
    assert backend
    # await backend.set_async("test", "rdtyfuhg", 1)  # type: ignore
    # value = await backend.get_async("test")
    # assert value
    # sleep(2)
    # value = await backend.get("test")
    # assert not value
