import typing as t
from abc import ABC

from starlette.concurrency import run_in_threadpool

from ..make_key_decorator import make_key_decorator, make_key_decorator_and_validate
from ..model import BaseCacheBackend


class BasePylibMemcachedCacheSync(BaseCacheBackend, ABC):
    _cache_client: t.Any

    @make_key_decorator
    def get(self, key: str, version: str = None) -> t.Any:
        return self._cache_client.get(key)

    @make_key_decorator_and_validate
    def set(
        self,
        key: str,
        value: t.Any,
        timeout: t.Union[float, int] = None,
        version: str = None,
    ) -> bool:
        result = self._cache_client.set(
            key, value, int(self.get_backend_timeout(timeout))
        )
        if not result:
            # Make sure the key doesn't keep its old value in case of failure
            # to set (memcached's 1MB limit).
            self._cache_client.delete(key)
            return False
        return bool(result)

    @make_key_decorator
    def delete(self, key: str, version: str = None) -> bool:
        result = self._cache_client.delete(key)
        return bool(result)

    @make_key_decorator
    def touch(
        self, key: str, timeout: t.Union[float, int] = None, version: str = None
    ) -> bool:
        result = self._cache_client.touch(key, self.get_backend_timeout(timeout))
        return bool(result)

    def close(self, **kwargs: t.Any) -> None:
        # Many clients don't clean up connections properly.
        self._cache_client.disconnect_all()

    def clear(self) -> None:
        self._cache_client.flush_all()


class BasePylibMemcachedCache(BasePylibMemcachedCacheSync):
    def __init__(
        self,
        server: t.List[str],
        library_client_type: t.Type,
        options: t.Dict = None,
        **kwargs: t.Any
    ):
        super().__init__(**kwargs)
        self._servers = server

        self._cache_client_class: t.Type = library_client_type
        self._cache_client_init: t.Any = None
        self._options = options or {}

    @property
    def client_servers(self) -> t.List[str]:
        return self._servers

    @property
    def _cache_client(self) -> t.Any:
        """
        Implement transparent thread-safe access to a memcached client.
        """
        if self._cache_client_init is None:
            self._cache_client_init = self._cache_client_class(
                self.client_servers, **self._options
            )
        return self._cache_client_init

    async def executor(self, func: t.Callable, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return await run_in_threadpool(func, *args, **kwargs)

    async def get_async(self, key: str, version: str = None) -> t.Any:
        return await self.executor(self.get, key, version=version)

    async def set_async(
        self,
        key: str,
        value: t.Any,
        timeout: t.Union[float, int] = None,
        version: str = None,
    ) -> bool:
        result = await self.executor(
            self.set, key, value, timeout=timeout, version=version
        )
        return bool(result)

    async def delete_async(self, key: str, version: str = None) -> bool:
        result = await self.executor(self.delete, key, version=version)
        return bool(result)

    async def touch_async(
        self, key: str, timeout: t.Union[float, int] = None, version: str = None
    ) -> bool:
        result = await self.executor(self.touch, key, timeout=timeout, version=version)
        return bool(result)

    async def close_async(self, **kwargs: t.Any) -> None:
        # Many clients don't clean up connections properly.
        await self.executor(self._cache_client.disconnect_all)

    async def clear_async(self) -> None:
        await self.executor(self._cache_client.flush_all)

    def validate_key(self, key: str) -> None:
        super().validate_key(key)
        self._memcache_key_warnings(key)
