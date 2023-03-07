# import pickle
# import typing as t
# from abc import ABC
#
# from ellar.helper.event_loop import get_or_create_eventloop
#
# try:
#     from aiomcache import Client
# except ImportError as e:  # pragma: no cover
#     raise RuntimeError(
#         "To use `AioMemCacheBackend`, you have to install 'aiomcache' package e.g. `pip install aiomcache`"
#     ) from e
#
# from ..interface import IBaseCacheBackendAsync
# from ..make_key_decorator import make_key_decorator, make_key_decorator_and_validate
# from ..model import BaseCacheBackend
# from .serializer import AioCacheSerializer, ICacheSerializer
#
#
# class _AioMemCacheBackendSync(IBaseCacheBackendAsync, ABC):
#     def _async_executor(self, func: t.Awaitable) -> t.Any:
#         return get_or_create_eventloop().run_until_complete(func)
#
#     def get(self, key: str, version: str = None) -> t.Any:
#         return self._async_executor(self.get_async(key, version=version))
#
#     def delete(self, key: str, version: str = None) -> bool:
#         res = self._async_executor(self.delete_async(key, version=version))
#         return bool(res)
#
#     def set(
#         self,
#         key: str,
#         value: t.Any,
#         timeout: t.Union[float, int] = None,
#         version: str = None,
#     ) -> bool:
#         res = self._async_executor(
#             self.set_async(key, value, version=version, timeout=timeout)
#         )
#         return bool(res)
#
#     def touch(
#         self, key: str, timeout: t.Union[float, int] = None, version: str = None
#     ) -> bool:
#         res = self._async_executor(
#             self.touch_async(key, version=version, timeout=timeout)
#         )
#         return bool(res)
#
#     def incr(self, key: str, delta: int = 1, version: str = None) -> int:
#         res = self._async_executor(self.incr_async(key, delta=delta, version=version))
#         return t.cast(int, res)
#
#     def decr(self, key: str, delta: int = 1, version: str = None) -> int:
#         res = self._async_executor(self.decr_async(key, delta=delta, version=version))
#         return t.cast(int, res)
#
#
# class AioMemCacheBackend(_AioMemCacheBackendSync, BaseCacheBackend):
#     """Memcached-based cache backend."""
#
#     pickle_protocol = pickle.HIGHEST_PROTOCOL
#     MEMCACHE_CLIENT: t.Type = Client
#
#     def __init__(
#         self,
#         host: str,
#         port: int = 11211,
#         pool_size: int = 2,
#         pool_minsize: int = None,
#         serializer: ICacheSerializer = None,
#         **kwargs: t.Any
#     ) -> None:
#         super().__init__(**kwargs)
#         self._client: Client = None  # type: ignore[assignment]
#         self._client_options = dict(
#             host=host, port=port, pool_size=pool_size, pool_minsize=pool_minsize
#         )
#         self._serializer = serializer or AioCacheSerializer()
#
#     def get_backend_timeout(self, timeout: t.Union[float, int] = None) -> int:
#         return int(super().get_backend_timeout(timeout))
#
#     @property
#     def _cache_client(self) -> Client:
#         if self._client is None:
#             self._client = self.MEMCACHE_CLIENT(**self._client_options)
#         return self._client
#
#     @make_key_decorator
#     async def get_async(self, key: str, version: str = None) -> t.Optional[t.Any]:
#         value = await self._cache_client.get(key.encode("utf-8"))
#         if value:
#             return self._serializer.load(value)
#         return None  # pragma: no cover
#
#     @make_key_decorator_and_validate
#     async def set_async(
#         self,
#         key: str,
#         value: t.Any,
#         timeout: t.Union[float, int] = None,
#         version: str = None,
#     ) -> bool:
#         return await self._cache_client.set(
#             key.encode("utf-8"),
#             self._serializer.dumps(value),
#             exptime=self.get_backend_timeout(timeout),
#         )
#
#     @make_key_decorator
#     async def delete_async(self, key: str, version: str = None) -> bool:
#         return await self._cache_client.delete(key.encode("utf-8"))
#
#     @make_key_decorator
#     async def touch_async(
#         self, key: str, timeout: t.Union[float, int] = None, version: str = None
#     ) -> bool:
#         return await self._cache_client.touch(
#             key.encode("utf-8"), exptime=self.get_backend_timeout(timeout)
#         )
#
#     @make_key_decorator
#     async def incr_async(self, key: str, delta: int = 1, version: str = None) -> int:
#         res = await self._cache_client.incr(key.encode("utf-8"), increment=delta)
#         return t.cast(int, res)
#
#     @make_key_decorator
#     async def decr_async(self, key: str, delta: int = 1, version: str = None) -> int:
#         res = await self._cache_client.decr(key.encode("utf-8"), decrement=delta)
#         return t.cast(int, res)
