import typing as t

from ellar.di import injectable

from .backends.simple_cache import SimpleCacheBackend
from .interface import ICacheService, ICacheServiceSync
from .model import BaseCacheBackend


class CacheServiceSync(ICacheServiceSync):
    _get_backend: t.Callable[..., BaseCacheBackend]

    def get(self, key: str, version: str = None, backend: str = None) -> t.Any:
        _backend = self._get_backend(backend)
        return _backend.get(key, version=version)

    def delete(self, key: str, version: str = None, backend: str = None) -> bool:
        _backend = self._get_backend(backend)
        return _backend.delete(key, version=version)

    def set(
        self,
        key: str,
        value: t.Any,
        timeout: int = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        _backend = self._get_backend(backend)
        return _backend.set(key, value, version=version, timeout=timeout)

    def touch(
        self, key: str, timeout: int = None, version: str = None, backend: str = None
    ) -> bool:
        _backend = self._get_backend(backend)
        return _backend.touch(key, version=version, timeout=timeout)

    def has_key(self, key: str, version: str = None, backend: str = None) -> bool:
        _backend = self._get_backend(backend)
        return _backend.touch(key, version=version)


@injectable  # type: ignore
class CacheService(CacheServiceSync, ICacheService):
    def __init__(self, backends: t.Dict[str, BaseCacheBackend] = None) -> None:
        if backends:
            assert backends.get(
                "default"
            ), "CACHES configuration must have a 'default' key."
        self._backends = backends or {
            "default": SimpleCacheBackend(key_prefix="ellar", version=1, timeout=300)
        }

    def _get_backend(self, backend: str = None) -> BaseCacheBackend:
        _backend = backend or "default"
        return self._backends[_backend]

    async def get_async(
        self, key: str, version: str = None, backend: str = None
    ) -> t.Any:
        _backend = self._get_backend(backend)
        return await _backend.get_async(key, version=version)

    async def delete_async(
        self, key: str, version: str = None, backend: str = None
    ) -> bool:
        _backend = self._get_backend(backend)
        return bool(await _backend.delete_async(key, version=version))

    async def set_async(
        self,
        key: str,
        value: t.Any,
        timeout: int = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        _backend = self._get_backend(backend)
        return await _backend.set_async(key, value, timeout=timeout, version=version)

    async def touch_async(
        self, key: str, timeout: int = None, version: str = None, backend: str = None
    ) -> bool:
        _backend = self._get_backend(backend)
        return await _backend.touch_async(key, timeout=timeout, version=version)

    async def has_key_async(
        self, key: str, version: str = None, backend: str = None
    ) -> bool:
        _backend = self._get_backend(backend)
        return await _backend.has_key_async(key, version=version)
