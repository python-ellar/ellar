import time


class MockAsyncMemCacheClient:
    def __init__(self, *args, time_lookup="ex", **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._time_lookup = time_lookup
        self._cache_default = {}

    @property
    def _cache(self):
        return self._cache_default

    def get_backend_timeout(self, timeout):
        return timeout

    async def set(self, *args, **kwargs):
        key, value = args
        self._cache[key] = (
            value,
            self.get_backend_timeout(kwargs.get(self._time_lookup)),
        )
        return True

    async def get(self, *args, **kwargs):
        (key,) = args
        _res = self._cache.get(key)

        if _res and time.time() >= _res[1]:
            del self._cache[key]
            _res = None
        return _res[0] if _res else None

    async def touch(self, *args, **kwargs):
        (key,) = args
        _res = self._cache.get(key)
        value = False
        if _res:
            self._cache.update(
                {
                    key: (
                        _res[0],
                        self.get_backend_timeout(kwargs.get(self._time_lookup)),
                    )
                }
            )
            value = True
        return value

    async def delete(self, *args, **kwargs):
        (key,) = args
        value = True
        if self._cache.get(key):
            del self._cache[key]
        else:
            value = False
        return value


class MockRedisClient(MockAsyncMemCacheClient):
    _cache_static = {}

    @property
    def _cache(self):
        return self._cache_static

    def get_backend_timeout(self, timeout):
        return time.time() + int(timeout)

    async def persist(self, key):
        return self._cache.get(key) is not None

    async def expire(self, key, ex):
        return await self.touch(key, ex=ex)
