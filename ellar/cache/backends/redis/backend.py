import random
import typing as t
from abc import ABC

from ellar.common.utils.event_loop import get_or_create_eventloop

try:
    from redis.asyncio import Redis
    from redis.asyncio.connection import ConnectionPool
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        "To use `RedisCacheBackend`, you have to install 'redis' package e.g. `pip install redis`"
    ) from e


from ...interface import IBaseCacheBackendAsync
from ...make_key_decorator import make_key_decorator, make_key_decorator_and_validate
from ...model import BaseCacheBackend
from ..serializer import ICacheSerializer, RedisSerializer


class _RedisCacheBackendSync(IBaseCacheBackendAsync, ABC):
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
        res = self._async_executor(self.set_async(key, value, version=version, ttl=ttl))
        return bool(res)

    def touch(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        res = self._async_executor(self.touch_async(key, version=version, ttl=ttl))
        return bool(res)

    def has_key(self, key: str, version: t.Optional[str] = None) -> bool:
        res = self._async_executor(self.has_key_async(key, version=version))
        return bool(res)

    def incr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        res = self._async_executor(self.incr_async(key, delta=delta, version=version))
        return t.cast(int, res)

    def decr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        res = self._async_executor(self.decr_async(key, delta=delta, version=version))
        return t.cast(int, res)


class RedisCacheBackend(_RedisCacheBackendSync, BaseCacheBackend):
    MEMCACHE_CLIENT: t.Type[Redis] = Redis
    """Redis-based cache backend.

    Redis Server Construct example::
        backend = RedisCacheBackend(servers=['redis://[[username]:[password]]@localhost:6379/0'])
        OR
        backend = RedisCacheBackend(servers=['redis://[[username]:[password]]@localhost:6379/0'])
        OR
        backend = RedisCacheBackend(servers=['rediss://[[username]:[password]]@localhost:6379/0'])
        OR
        backend = RedisCacheBackend(servers=['unix://[username@]/path/to/socket.sock?db=0[&password=password]'])

    """

    def __init__(
        self,
        servers: t.List[str],
        options: t.Optional[t.Dict] = None,
        serializer: t.Optional[ICacheSerializer] = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)

        self._pools: t.Dict[int, ConnectionPool] = {}
        self._servers = servers
        _default_options = options or {}
        self._options = {
            **_default_options,
        }
        self._serializer = serializer or RedisSerializer()

    def _get_connection_pool_index(self, write: bool) -> int:
        # Write to the first server. Read from other servers if there are more,
        # otherwise read from the first server.
        if write or len(self._servers) == 1:
            return 0
        return random.randint(1, len(self._servers) - 1)

    def _get_connection_pool(self, write: bool) -> ConnectionPool:
        index = self._get_connection_pool_index(write)
        if index not in self._pools:
            self._pools[index] = ConnectionPool.from_url(
                self._servers[index],
                **self._options,
            )
        return self._pools[index]

    def _get_client(self, *, write: bool = False) -> Redis:
        # key is used so that the method signature remains the same and custom
        # cache client can be implemented which might require the key to select
        # the server, e.g. sharding.
        pool = self._get_connection_pool(write)
        return self.MEMCACHE_CLIENT(connection_pool=pool)

    def get_backend_ttl(
        self, ttl: t.Union[float, int, None] = None
    ) -> t.Union[float, int]:
        if ttl is None:
            ttl = self._default_ttl
        # The key will be made persistent if None used as a ttl.
        # Non-positive values will cause the key to be deleted.
        return None if ttl is None else max(0, int(ttl))

    @make_key_decorator
    async def get_async(self, key: str, version: t.Optional[str] = None) -> t.Any:
        client = self._get_client()
        value = await client.get(key)
        if value is not None:
            return self._serializer.load(value)
        return None

    @make_key_decorator_and_validate
    async def set_async(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        client = self._get_client()
        value = self._serializer.dumps(value)
        if ttl == 0:
            await client.delete(key)

        return bool(await client.set(key, value, ex=self.get_backend_ttl(ttl)))

    @make_key_decorator
    async def delete_async(self, key: str, version: t.Optional[str] = None) -> bool:
        client = self._get_client()
        result = await client.delete(key)
        return bool(result)

    @make_key_decorator
    async def touch_async(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        client = self._get_client()
        if ttl is None:
            res = await client.persist(key)
            return bool(res)

        res = await client.expire(key, int(self.get_backend_ttl(ttl)))
        return bool(res)

    @make_key_decorator
    async def has_key_async(self, key: str, version: t.Optional[str] = None) -> bool:
        client = self._get_client()
        res = await client.exists(key)
        return bool(res)

    @make_key_decorator
    async def incr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        client = self._get_client()
        res = await client.incr(key, amount=delta)
        return res

    @make_key_decorator
    async def decr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        client = self._get_client()
        res = await client.decr(key, amount=delta)
        return res
