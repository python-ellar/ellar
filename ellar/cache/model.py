import time
import typing as t
import warnings
from abc import ABC

from .interface import IBaseCacheBackendAsync, IBaseCacheBackendSync


class CacheKeyWarning(RuntimeWarning):
    pass


class BaseCacheBackend(IBaseCacheBackendSync, IBaseCacheBackendAsync, ABC):
    MEMCACHE_MAX_KEY_LENGTH = 250

    def __init__(
        self,
        key_prefix: t.Optional[str] = None,
        version: t.Optional[int] = None,
        ttl: t.Optional[int] = None,
    ) -> None:
        self._key_prefix = key_prefix or ""
        self._version = version or 1
        self._default_ttl = int(ttl) if ttl else 300

    @property
    def key_prefix(self) -> str:
        return self._key_prefix

    async def has_key_async(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """
        return await self.get_async(key, version=version) is not None

    def has_key(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """
        return self.get(key, version=version) is not None

    def validate_key(self, key: str) -> None:
        if len(key) > self.MEMCACHE_MAX_KEY_LENGTH:
            warnings.warn(
                "Cache key will cause errors if used with memcached: %r "
                "(longer than %s)" % (key, self.MEMCACHE_MAX_KEY_LENGTH),
                CacheKeyWarning,
                stacklevel=3,
            )

    def _memcache_key_warnings(self, key: str) -> None:
        for char in key:
            if ord(char) < 33 or ord(char) == 127:
                warnings.warn(
                    "Cache key contains characters that will cause errors if "
                    "used with memcached: %r" % key,
                    CacheKeyWarning,
                    stacklevel=3,
                )
                break

    def make_key(self, key: str, version: t.Optional[str] = None) -> str:
        """
        Default function to generate keys.
        Construct the key used by all other methods. By default, prepend
        the `key_prefix`.
        """
        return "%s:%s:%s" % (self._key_prefix, version or self._version, key)

    def get_backend_ttl(
        self, ttl: t.Union[float, int, None] = None
    ) -> t.Union[float, int]:
        """
        Return the timeout value usable by this backend based upon the provided
        timeout.
        """
        if ttl is None:
            ttl = self._default_ttl
        elif ttl == 0:
            # avoid time.time() related precision issues
            ttl = -1
        return time.time() + ttl
