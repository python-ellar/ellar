import typing as t
from abc import ABC, abstractmethod

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.cache.model import BaseCacheBackend


class IBaseCacheBackendAsync(ABC):
    @abstractmethod
    async def get_async(self, key: str, version: t.Optional[str] = None) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    async def delete_async(self, key: str, version: t.Optional[str] = None) -> bool:
        """Delete `key` from the cache.
        :param key: the key to delete.
        :param version: the version for the key
        :returns: Whether the key existed and has been deleted.
        :rtype: boolean
        """

    @abstractmethod
    async def set_async(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param ttl: the cache ttl for the key in seconds (if not
                        specified, it uses the default ttl). A ttl of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """

    @abstractmethod
    async def touch_async(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """
        Update the key's expiry time using ttl. Return True if successful
        or False if the key does not exist.
        """

    @abstractmethod
    async def has_key_async(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """

    @abstractmethod
    async def incr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        """
        Increments the number stored at key by one. If the key does not exist, it is set to 0
        """

    @abstractmethod
    async def decr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        """
        Decrements the number stored at key by one. If the key does not exist, it is set to 0
        """


class IBaseCacheBackendSync(ABC):
    @abstractmethod
    def get(self, key: str, version: t.Optional[str] = None) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    def delete(self, key: str, version: t.Optional[str] = None) -> bool:
        """Delete `key` from the cache.
        :param key: the key to delete.
        :param version: the version for the key
        :returns: Whether the key existed and has been deleted.
        :rtype: boolean
        """

    @abstractmethod
    def set(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param ttl: the cache ttl for the key in seconds (if not
                        specified, it uses the default ttl). A ttl of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """

    @abstractmethod
    def touch(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """
        Update the key's expiry time using ttl. Return True if successful
        or False if the key does not exist.
        """

    @abstractmethod
    def has_key(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """

    @abstractmethod
    def incr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        """
        Increments the number stored at key by one. If the key does not exist, it is set to 0
        """

    @abstractmethod
    def decr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        """
        Decrements the number stored at key by one. If the key does not exist, it is set to 0
        """


class ICacheServiceSync(ABC):
    @abstractmethod
    def get(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :param backend: a backend service name
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    def delete(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """Delete `key` from the cache.
        :param key: the key to delete.
        :param version: the version for the key
        :param backend: a backend service name
        :returns: Whether the key existed and has been deleted.
        :rtype: boolean
        """

    @abstractmethod
    def set(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param backend: a backend service name
        :param ttl: the cache ttl for the key in seconds (if not
                        specified, it uses the default ttl). A ttl of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """

    @abstractmethod
    def touch(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        """
        Update the key's expiry time using ttl. Return True if successful
        or False if the key does not exist.
        """

    @abstractmethod
    def has_key(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """

    @abstractmethod
    def incr(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        """
        Increments the number stored at key by one. If the key does not exist, it is set to 0
        """

    @abstractmethod
    def decr(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        """
        Decrements the number stored at key by one. If the key does not exist, it is set to 0
        """


class ICacheServiceAsync(ABC):
    @abstractmethod
    async def get_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :param backend: a backend service name
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    async def delete_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """Delete `key` from the cache.
        :param key: the key to delete.
        :param version: the version for the key
        :param backend: a backend service name
        :returns: Whether the key existed and has been deleted.
        :rtype: boolean
        """

    @abstractmethod
    async def set_async(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param backend: a backend service name
        :param ttl: the cache ttl for the key in seconds (if not
                        specified, it uses the default ttl). A ttl of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """

    @abstractmethod
    async def touch_async(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> bool:
        """
        Update the key's expiry time using ttl. Return True if successful
        or False if the key does not exist.
        """

    @abstractmethod
    async def has_key_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """

    @abstractmethod
    async def incr_async(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        """
        Increments the number stored at key by one. If the key does not exist, it is set to 0
        """

    @abstractmethod
    async def decr_async(
        self,
        key: str,
        delta: int = 1,
        version: t.Optional[str] = None,
        backend: t.Optional[str] = None,
    ) -> int:
        """
        Decrements the number stored at key by one. If the key does not exist, it is set to 0
        """


class ICacheService(ICacheServiceSync, ICacheServiceAsync, ABC):
    """Cache Service Interface"""

    @abstractmethod
    def get_backend(self, backend: t.Optional[str] = None) -> "BaseCacheBackend":
        """
        Return a given Cache Backend configured by configuration backend name.
        :param backend: Cache Backend configuration name. If not set, 'default' backend will be returned
        :return: BaseCacheBackend
        """
