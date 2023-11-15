import pickle
import time
import typing as t
from abc import ABC
from collections import OrderedDict

from anyio import Lock
from ellar.common.utils.event_loop import get_or_create_eventloop

from ..interface import IBaseCacheBackendAsync
from ..make_key_decorator import make_key_decorator, make_key_decorator_and_validate
from ..model import BaseCacheBackend


class _LocalMemCacheBackendSync(IBaseCacheBackendAsync, ABC):
    def _async_executor(self, func: t.Awaitable) -> t.Any:
        return get_or_create_eventloop().run_until_complete(func)

    def get(self, key: str, version: t.Optional[str] = None) -> t.Any:
        return self._async_executor(self.get_async(key, version=version))

    def delete(self, key: str, version: t.Optional[str] = None) -> bool:
        res = self._async_executor(self.delete_async(key, version=version))
        return bool(res)

    def set(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        res = self._async_executor(self.set_async(key, value, ttl=ttl, version=version))
        return bool(res)

    def touch(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        res = self._async_executor(self.touch_async(key, ttl=ttl, version=version))
        return bool(res)

    def incr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        res = self._async_executor(self.incr_async(key, delta=delta, version=version))
        return t.cast(int, res)

    def decr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        res = self._async_executor(self.decr_async(key, delta=delta, version=version))
        return t.cast(int, res)


class LocalMemCacheBackend(_LocalMemCacheBackendSync, BaseCacheBackend):
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, **kwargs: t.Any) -> None:
        super().__init__(**kwargs)
        self._cache: t.Dict[str, bytes] = OrderedDict()
        self._expire_track: t.Dict[str, float] = {}
        self._lock = Lock()

    @make_key_decorator
    async def get_async(self, key: str, version: t.Optional[str] = None) -> t.Any:
        async with self._lock:
            if self._has_expired(key):
                await self._delete(key)
                return None

            pickled = self._cache[key]
            return pickle.loads(pickled)

    async def _delete(self, key: str) -> bool:
        try:
            self._cache.pop(key)
            self._expire_track.pop(key)
        except KeyError:
            return False
        return True

    @make_key_decorator
    async def delete_async(self, key: str, version: t.Optional[str] = None) -> bool:
        async with self._lock:
            return await self._delete(key)

    @make_key_decorator_and_validate
    async def set_async(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        async with self._lock:
            self._cache[key] = pickle.dumps(value, self.pickle_protocol)
            self._expire_track[key] = self.get_backend_ttl(ttl)
            return True

    def _has_expired(self, key: str) -> bool:
        exp = self._expire_track.get(key, -1)
        return exp is not None and exp <= time.time()

    @make_key_decorator
    async def has_key_async(self, key: str, version: t.Optional[str] = None) -> bool:
        async with self._lock:
            if self._has_expired(key):
                await self._delete(key)
                return False
            return True

    @make_key_decorator
    async def touch_async(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        async with self._lock:
            if self._has_expired(key):
                return False

            self._expire_track[key] = self.get_backend_ttl(ttl)
            return True

    def has_key(self, key: str, version: t.Optional[str] = None) -> bool:
        res = self._async_executor(self.has_key_async(key, version=version))
        return bool(res)

    def _incr_decr_action(self, key: str, delta: int) -> int:
        pickled = self._cache[key]
        value = t.cast(int, pickle.loads(pickled))
        new_value = value + delta
        pickled = pickle.dumps(new_value, self.pickle_protocol)
        self._cache[key] = pickled
        return new_value

    @make_key_decorator
    async def incr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        async with self._lock:
            if self._has_expired(key):
                await self._delete(key)
                raise ValueError("Key '%s' not found" % key)
            return self._incr_decr_action(key, delta)

    @make_key_decorator
    async def decr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        async with self._lock:
            if self._has_expired(key):
                await self._delete(key)
                raise ValueError("Key '%s' not found" % key)
            res = self._incr_decr_action(key, delta * -1)
            if res < 0:
                return self._incr_decr_action(key, res * -1)
            return res
