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
        key_prefix: str = None,
        version: int = None,
        timeout: int = None,
    ) -> None:
        self._key_prefix = key_prefix or ""
        self._version = version or 1
        self._default_timeout = int(timeout) if timeout else 300

    async def has_key_async(self, key: str, version: str = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """
        return await self.get_async(key, version) is not None

    def has_key(self, key: str, version: str = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """
        return self.get(key, version) is not None

    def validate_key(self, key: str) -> None:
        if len(key) > self.MEMCACHE_MAX_KEY_LENGTH:
            warnings.warn(
                "Cache key will cause errors if used with memcached: %r "
                "(longer than %s)" % (key, self.MEMCACHE_MAX_KEY_LENGTH),
                CacheKeyWarning,
            )

    def _memcache_key_warnings(self, key: str) -> None:
        for char in key:
            if ord(char) < 33 or ord(char) == 127:
                warnings.warn(
                    "Cache key contains characters that will cause errors if "
                    "used with memcached: %r" % key,
                    CacheKeyWarning,
                )
                break

    def make_key(self, key: str, version: str = None) -> str:
        """
        Default function to generate keys.
        Construct the key used by all other methods. By default, prepend
        the `key_prefix`.
        """
        return "%s:%s:%s" % (self._key_prefix, version or self._version, key)

    def get_backend_timeout(
        self, timeout: t.Union[float, int] = None
    ) -> t.Union[float, int]:
        """
        Return the timeout value usable by this backend based upon the provided
        timeout.
        """
        if timeout is None:
            timeout = self._default_timeout
        elif timeout == 0:
            # avoid time.time() related precision issues
            timeout = -1
        return time.time() + timeout
