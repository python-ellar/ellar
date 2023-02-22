import typing as t
from abc import ABC, abstractmethod

if t.TYPE_CHECKING:
    from ellar.cache.model import BaseCacheBackend


class IBaseCacheBackendAsync(ABC):
    @abstractmethod
    async def get_async(self, key: str, version: str = None) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    async def delete_async(self, key: str, version: str = None) -> bool:
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
        timeout: t.Union[float, int] = None,
        version: str = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """

    @abstractmethod
    async def touch_async(
        self, key: str, timeout: t.Union[float, int] = None, version: str = None
    ) -> bool:
        """
        Update the key's expiry time using timeout. Return True if successful
        or False if the key does not exist.
        """


class IBaseCacheBackendSync(ABC):
    @abstractmethod
    def get(self, key: str, version: str = None) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    def delete(self, key: str, version: str = None) -> bool:
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
        timeout: t.Union[float, int] = None,
        version: str = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
                        0 indicates that the cache never expires.
        :returns: ``True`` if key has been updated, ``False`` for backend
                  errors. Pickling errors, however, will raise a subclass of
                  ``pickle.PickleError``.
        :rtype: boolean
        """

    @abstractmethod
    def touch(
        self, key: str, timeout: t.Union[float, int] = None, version: str = None
    ) -> bool:
        """
        Update the key's expiry time using timeout. Return True if successful
        or False if the key does not exist.
        """


class ICacheServiceSync(ABC):
    @abstractmethod
    def get(self, key: str, version: str = None, backend: str = None) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :param backend: a backend service name
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    def delete(self, key: str, version: str = None, backend: str = None) -> bool:
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
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param backend: a backend service name
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
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
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        """
        Update the key's expiry time using timeout. Return True if successful
        or False if the key does not exist.
        """

    @abstractmethod
    def has_key(self, key: str, version: str = None, backend: str = None) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """


class ICacheServiceAsync(ABC):
    @abstractmethod
    async def get_async(
        self, key: str, version: str = None, backend: str = None
    ) -> t.Any:
        """Look up key in the cache and return the value for it.
        :param key: the key to be looked up.
        :param version: the version for the key
        :param backend: a backend service name
        :returns: The value if it exists and is readable, else ``None``.
        """

    @abstractmethod
    async def delete_async(
        self, key: str, version: str = None, backend: str = None
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
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        """Add a new key/value to the cache (overwrites value, if key already
        exists in the cache).
        :param key: the key to set
        :param value: the value for the key
        :param version: the version for the key
        :param backend: a backend service name
        :param timeout: the cache timeout for the key in seconds (if not
                        specified, it uses the default timeout). A timeout of
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
        timeout: t.Union[float, int] = None,
        version: str = None,
        backend: str = None,
    ) -> bool:
        """
        Update the key's expiry time using timeout. Return True if successful
        or False if the key does not exist.
        """

    @abstractmethod
    async def has_key_async(
        self, key: str, version: str = None, backend: str = None
    ) -> bool:
        """
        Return True if the key is in the cache and has not expired.
        """


class ICacheService(ICacheServiceSync, ICacheServiceAsync, ABC):
    """Cache Service Interface"""

    def get_backend(self, backend: str = None) -> "BaseCacheBackend":
        """
        Return a given Cache Backend configured by configuration backend name.
        :param backend: Cache Backend configuration name. If not set, 'default' backend will be returned
        :return: BaseCacheBackend
        """
