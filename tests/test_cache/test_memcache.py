from ellar.cache.backends.aio_cache import AioMemCacheBackend


# @pytest.mark.asyncio
def test_aio_mem_cache(anyio_backend):
    backend = AioMemCacheBackend("localhost", port=11211)
    assert backend
    # backend.set("test", "values", timeout=10)
    # res = backend.get("test")
    # assert res == "values"
