import typing as t
from abc import ABC, abstractmethod

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.cache.model import BaseCacheBackend


class IBaseCacheBackendAsync(ABC):
    @abstractmethod
    async def get_async(self, key: str, version: t.Optional[str] = None) -> t.Any:
        """
        Look up key in the cache and return the value for it.

        :param key: The key to be looked up.
        :param version: The version for the key.
        :return: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    async def delete_async(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Delete `key` from the cache.

        :param key: The key to delete.
        :param version: The version for the key.
        :return: Whether the key existed and has been deleted.
        """

    @abstractmethod
    async def set_async(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """
        Add a new key/value to the cache (overwrites value, if key already exists in the cache).

        :param key: The key to set.
        :param value: The value to be cached.
        :param ttl: The cache time-to-live for the key in seconds.
                    If not specified, the default TTL is used.
                    A TTL of 0 indicates that the cache never expires.
        :param version: The version for the key.
        :return: ``True`` if key has been updated, ``False`` for backend errors.
                 Pickling errors, however, will raise a subclass of ``pickle.PickleError``.
        """

    @abstractmethod
    async def touch_async(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """
        Update the key's expiry time using ttl.

        :param key: The key to update.
        :param ttl: The new time-to-live.
        :param version: The version for the key.
        :return: `True` if successful or `False` if the key does not exist.
        """

    @abstractmethod
    async def has_key_async(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.

        :param key: The key to check.
        :param version: The version for the key.
        :return: `True` if key is found and not expired, else `False`.
        """

    @abstractmethod
    async def incr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        """
        Increments the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to increment.
        :param delta: The amount to increment by.
        :param version: The version for the key.
        :return: The new value.
        """

    @abstractmethod
    async def decr_async(
        self, key: str, delta: int = 1, version: t.Optional[str] = None
    ) -> int:
        """
        Decrements the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to decrement.
        :param delta: The amount to decrement by.
        :param version: The version for the key.
        :return: The new value.
        """


class IBaseCacheBackendSync(ABC):
    @abstractmethod
    def get(self, key: str, version: t.Optional[str] = None) -> t.Any:
        """
        Look up key in the cache and return the value for it.

        :param key: The key to be looked up.
        :param version: The version for the key.
        :return: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    def delete(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Delete `key` from the cache.

        :param key: The key to delete.
        :param version: The version for the key.
        :return: Whether the key existed and has been deleted.
        """

    @abstractmethod
    def set(
        self,
        key: str,
        value: t.Any,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """
        Add a new key/value to the cache (overwrites value, if key already exists in the cache).

        :param key: The key to set.
        :param value: The value to be cached.
        :param ttl: The cache time-to-live for the key in seconds.
                    If not specified, the default TTL is used.
                    A TTL of 0 indicates that the cache never expires.
        :param version: The version for the key.
        :return: ``True`` if key has been updated, ``False`` for backend errors.
                 Pickling errors, however, will raise a subclass of ``pickle.PickleError``.
        """

    @abstractmethod
    def touch(
        self,
        key: str,
        ttl: t.Union[float, int, None] = None,
        version: t.Optional[str] = None,
    ) -> bool:
        """
        Update the key's expiry time using ttl.

        :param key: The key to update.
        :param ttl: The new time-to-live.
        :param version: The version for the key.
        :return: `True` if successful or `False` if the key does not exist.
        """

    @abstractmethod
    def has_key(self, key: str, version: t.Optional[str] = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.

        :param key: The key to check.
        :param version: The version for the key.
        :return: `True` if key is found and not expired, else `False`.
        """

    @abstractmethod
    def incr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        """
        Increments the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to increment.
        :param delta: The amount to increment by.
        :param version: The version for the key.
        :return: The new value.
        """

    @abstractmethod
    def decr(self, key: str, delta: int = 1, version: t.Optional[str] = None) -> int:
        """
        Decrements the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to decrement.
        :param delta: The amount to decrement by.
        :param version: The version for the key.
        :return: The new value.
        """


class ICacheServiceSync(ABC):
    @abstractmethod
    def get(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> t.Any:
        """
        Look up key in the cache and return the value for it.

        :param key: The key to be looked up.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    def delete(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """
        Delete `key` from the cache.

        :param key: The key to delete.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: Whether the key existed and has been deleted.
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
        """
        Add a new key/value to the cache (overwrites value, if key already exists in the cache).

        :param key: The key to set.
        :param value: The value to be cached.
        :param ttl: The cache time-to-live for the key in seconds.
                    If not specified, the default TTL is used.
                    A TTL of 0 indicates that the cache never expires.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: ``True`` if key has been updated, ``False`` for backend errors.
                 Pickling errors, however, will raise a subclass of ``pickle.PickleError``.
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
        Update the key's expiry time using ttl.

        :param key: The key to update.
        :param ttl: The new time-to-live.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: `True` if successful or `False` if the key does not exist.
        """

    @abstractmethod
    def has_key(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """
        Return True if the key is in the cache and has not expired.

        :param key: The key to check.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: `True` if key is found and not expired, else `False`.
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
        Increments the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to increment.
        :param delta: The amount to increment by.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: The new value.
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
        Decrements the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to decrement.
        :param delta: The amount to decrement by.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: The new value.
        """


class ICacheServiceAsync(ABC):
    @abstractmethod
    async def get_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> t.Any:
        """
        Look up key in the cache and return the value for it.

        :param key: The key to be looked up.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    async def delete_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """
        Delete `key` from the cache.

        :param key: The key to delete.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: Whether the key existed and has been deleted.
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
        """
        Add a new key/value to the cache (overwrites value, if key already exists in the cache).

        :param key: The key to set.
        :param value: The value to be cached.
        :param ttl: The cache time-to-live for the key in seconds.
                    If not specified, the default TTL is used.
                    A TTL of 0 indicates that the cache never expires.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: ``True`` if key has been updated, ``False`` for backend errors.
                 Pickling errors, however, will raise a subclass of ``pickle.PickleError``.
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
        Update the key's expiry time using ttl.

        :param key: The key to update.
        :param ttl: The new time-to-live.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: `True` if successful or `False` if the key does not exist.
        """

    @abstractmethod
    async def has_key_async(
        self, key: str, version: t.Optional[str] = None, backend: t.Optional[str] = None
    ) -> bool:
        """
        Return True if the key is in the cache and has not expired.

        :param key: The key to check.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: `True` if key is found and not expired, else `False`.
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
        Increments the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to increment.
        :param delta: The amount to increment by.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: The new value.
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
        Decrements the number stored at key by one. If the key does not exist, it is set to 0.

        :param key: The key to decrement.
        :param delta: The amount to decrement by.
        :param version: The version for the key.
        :param backend: The name of the backend service to use.
        :return: The new value.
        """


class ICacheService(ICacheServiceSync, ICacheServiceAsync, ABC):
    """Cache Service Interface"""

    @abstractmethod
    def get_backend(self, backend: t.Optional[str] = None) -> "BaseCacheBackend":
        """
        Return a given Cache Backend configured by configuration backend name.

        :param backend: Cache Backend configuration name. If not set, 'default' backend will be returned.
        :return: BaseCacheBackend
        """
