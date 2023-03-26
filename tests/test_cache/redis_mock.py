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

    def get_backend_ttl(self, ttl):
        return ttl

    async def set(self, *args, **kwargs):
        key, value = args
        self._cache[key] = (
            value,
            self.get_backend_ttl(kwargs.get(self._time_lookup)),
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
                        self.get_backend_ttl(kwargs.get(self._time_lookup)),
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

    async def _incr_decr_action(self, key: str, delta: int) -> int:
        value, _time = self._cache.get(key, (0, 0))
        if _time == 0:
            await self.set(key, 0)
            return 0

        new_value = value + delta
        self._cache[key] = new_value, _time
        return new_value

    async def incr(self, key: str, amount: int = 1, **kwargs) -> int:
        return await self._incr_decr_action(key, amount)

    async def decr(self, key: str, amount: int = 1, **kwargs) -> int:
        res = await self._incr_decr_action(key, amount * -1)
        if res < 0:
            return await self._incr_decr_action(key, res * -1)
        return res


class MockRedisClient(MockAsyncMemCacheClient):
    _cache_static = {}

    @property
    def _cache(self):
        return self._cache_static

    def get_backend_ttl(self, ttl):
        return time.time() + int(ttl)

    async def persist(self, key):
        return self._cache.get(key) is not None

    async def exists(self, key):
        return self._cache.get(key) is not None

    async def expire(self, key, ex):
        return await self.touch(key, ex=ex)
