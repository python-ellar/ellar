import typing as t

from ellar.di import injectable

from .backends.local_cache import LocalMemCacheBackend
from .interface import ICacheService, ICacheServiceSync
from .model import BaseCacheBackend


class InvalidCacheBackendKeyException(Exception):
    pass


class _CacheServiceSync(ICacheServiceSync):
    def incr(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        _backend = self.get_backend(backend)
        return _backend.incr(key, delta=delta, version=version)

    def decr(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        _backend = self.get_backend(backend)
        return _backend.decr(key, delta=delta, version=version)

    get_backend: t.Callable[..., BaseCacheBackend]

    def get(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> t.Any:
        _backend = self.get_backend(backend)
        return _backend.get(key, version=version)

    def delete(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        _backend = self.get_backend(backend)
        return _backend.delete(key, version=version)

    def set(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return _backend.set(key, value, version=version, ttl=ttl)

    def touch(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return _backend.touch(key, version=version, ttl=ttl)

    def has_key(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        _backend = self.get_backend(backend)
        return _backend.has_key(key, version=version)


@injectable
class CacheService(_CacheServiceSync, ICacheService):
    """
    A Cache Backend Service that wraps Ellar cache backends
    """

    def __init__(
        self, backends: t.Optional[t.Dict[str, BaseCacheBackend]] = None
    ) -> None:
        if backends:
            assert backends.get(
                "default"
            ), "CACHES configuration must have a 'default' key."
        self._backends = backends or {
            "default": LocalMemCacheBackend(key_prefix="ellar", version=1, ttl=300)
        }

    def get_backend(self, backend: t.Optional[str] = None) -> BaseCacheBackend:
        _backend = backend or "default"
        try:
            return self._backends[_backend]
        except KeyError as kex:
            raise InvalidCacheBackendKeyException(
                f"There is no backend configured with the name: '{_backend}'"
            ) from kex

    async def get_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> t.Any:
        _backend = self.get_backend(backend)
        return await _backend.get_async(key, version=version)

    async def delete_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        _backend = self.get_backend(backend)
        return bool(await _backend.delete_async(key, version=version))

    async def set_async(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return await _backend.set_async(key, value, ttl=ttl, version=version)

    async def touch_async(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        _backend = self.get_backend(backend)
        return await _backend.touch_async(key, ttl=ttl, version=version)

    async def has_key_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        _backend = self.get_backend(backend)
        return await _backend.has_key_async(key, version=version)

    async def incr_async(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        _backend = self.get_backend(backend)
        return await _backend.incr_async(key, delta=delta, version=version)

    async def decr_async(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        _backend = self.get_backend(backend)
        return await _backend.decr_async(key, delta=delta, version=version)
