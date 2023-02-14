import asyncio
import pickle
import typing as t
from abc import ABC

try:
    from redis.asyncio import Redis  # type: ignore
    from redis.asyncio.connection import ConnectionPool  # type: ignore
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        "To use `RedisCacheBackend`, you have to install 'redis' package e.g. `pip install redis`"
    ) from e
from ..interface import IBaseCacheBackendAsync
from ..make_key_decorator import make_key_decorator
from ..model import BaseCacheBackend


class RedisCacheBackendSync(IBaseCacheBackendAsync, ABC):
    def _async_executor(self, func: t.Awaitable) -> t.Any:
        return asyncio.get_event_loop().run_until_complete(func)

    def get(self, key: str, version: str = None) -> t.Any:
        return self._async_executor(self.get_async(key, version=version))

    def delete(self, key: str, version: str = None) -> bool:
        res = self._async_executor(self.delete_async(key, version=version))
        return bool(res)

    def set(
        self, key: str, value: t.Any, timeout: int = None, version: str = None
    ) -> bool:
        res = self._async_executor(
            self.set_async(key, value, version=version, timeout=timeout)
        )
        return bool(res)

    def touch(self, key: str, timeout: int = None, version: str = None) -> bool:
        res = self._async_executor(
            self.touch_async(key, version=version, timeout=timeout)
        )
        return bool(res)


class RedisCacheBackend(RedisCacheBackendSync, BaseCacheBackend):
    """Redis-based cache backend."""

    pickle_protocol: t.Any = pickle.HIGHEST_PROTOCOL

    def __init__(
        self,
        url: str = "localhost",
        db: int = None,
        port: int = None,
        username: str = None,
        password: str = None,
        options: t.Dict = None,
        serializer: t.Callable = pickle.dumps,
        deserializer: t.Callable = pickle.loads,
        **kwargs: t.Any
    ) -> None:
        super().__init__(**kwargs)

        self._cache_client_init: Redis = None
        _default_options = options or {}
        self._options = {
            "url": url,
            "db": db,
            "port": port,
            "username": username,
            "password": password,
            **_default_options,
        }
        self._serializer = serializer
        self._deserializer = deserializer

    def get_backend_timeout(self, timeout: int = None) -> t.Union[float, int]:
        if timeout is None:
            timeout = self._default_timeout
        # The key will be made persistent if None used as a timeout.
        # Non-positive values will cause the key to be deleted.
        return None if timeout is None else max(0, int(timeout))

    @property
    def _cache_client(self) -> Redis:
        """
        Implement transparent thread-safe access to a memcached client.
        """
        if self._cache_client_init is None:
            pool = ConnectionPool.from_url(**self._options)
            self._redis_int = Redis(connection_pool=pool)
        return self._cache_client_init

    @make_key_decorator
    async def get_async(self, key: str, version: str = None) -> t.Any:
        value = await self._cache_client.get(key)
        if value:
            return self._deserializer(value)
        return None

    @make_key_decorator
    async def set_async(
        self, key: str, value: t.Any, timeout: int = None, version: str = None
    ) -> bool:
        value = self._serializer(value, self.pickle_protocol)
        if timeout == 0:
            await self._cache_client.delete(key)

        return bool(
            await self._cache_client.set(
                key, value, ex=self.get_backend_timeout(timeout)
            )
        )

    @make_key_decorator
    async def delete_async(self, key: str, version: str = None) -> bool:
        result = await self._cache_client.delete(key)
        return bool(result)

    @make_key_decorator
    async def touch_async(
        self, key: str, timeout: int = None, version: str = None
    ) -> bool:
        if timeout is None:
            res = await self._cache_client.persist(key)
            return bool(res)
        res = await self._cache_client.expire(key, self.get_backend_timeout(timeout))
        return bool(res)
