import dataclasses
import typing as t

from ellar.cache.interface import ICacheService
from ellar.common import (
    EllarInterceptor,
    IExecutionContext,
    UseInterceptors,
    set_metadata,
)
from ellar.common.constants import ROUTE_CACHE_OPTIONS
from ellar.core import Reflector
from ellar.di import injectable


@dataclasses.dataclass
class RouteCacheOptions:
    """
    Cache Options for Route handlers
    """

    ttl: t.Union[int, float]
    key_prefix: str
    make_key_callback: t.Callable[[IExecutionContext, str], str]
    version: t.Optional[str] = None
    backend: str = "default"


def _route_cache_make_key(context: IExecutionContext, key_prefix: str) -> str:
    """Defaults key generator for caching view"""
    connection = context.switch_to_http_connection()
    return f"{connection.get_client().url}:{key_prefix or 'view'}"


@injectable
class _CacheEllarInterceptor(EllarInterceptor):
    __slots__ = (
        "_cache_service",
        "_reflector",
    )

    def __init__(self, cache_service: ICacheService, reflector: "Reflector") -> None:
        self._cache_service = cache_service
        self._reflector = reflector

    async def intercept(
        self, context: IExecutionContext, next_interceptor: t.Callable[..., t.Coroutine]
    ) -> t.Any:
        opts: RouteCacheOptions = self._reflector.get(
            ROUTE_CACHE_OPTIONS, context.get_handler()
        )

        backend = self._cache_service.get_backend(backend=opts.backend)
        key = opts.make_key_callback(context, opts.key_prefix or backend.key_prefix)

        cached_value = await self._cache_service.get_async(
            key, opts.version, backend=opts.backend
        )
        if cached_value:
            return cached_value

        response = await next_interceptor()
        await self._cache_service.set_async(
            key,
            response,
            ttl=opts.ttl,
            version=opts.version,
            backend=opts.backend,
        )
        return response


def Cache(
    ttl: t.Union[float, int],
    *,
    key_prefix: str = "",
    version: t.Optional[str] = None,
    backend: str = "default",
    make_key_callback: t.Optional[t.Callable[[IExecutionContext, str], str]] = None,
) -> t.Callable:
    """
    Decorates a controller or route function to cache its response.

    :param ttl: The time-to-live for the cache in seconds.
    :param key_prefix: A prefix to identify the cache key.
    :param version: A version string to be used in constructing the key.
    :param backend: The name of the cache backend to use. Defaults to `default`.
    :param make_key_callback: A callable to dynamically construct the cache key.
    :return: A callable decorator.

    Examples:
    ---------
    ```python
    from ellar.common import get, Controller
    from ellar.cache import Cache

    @Controller
    class MyController:
        @get("/cached-route")
        @Cache(ttl=60, key_prefix="my_route")
        def cached_route(self):
            return {"message": "This response is cached for 60 seconds"}

        @get("/dynamic-key")
        @Cache(ttl=300, make_key_callback=lambda ctx, prefix: f"{prefix}:{ctx.switch_to_http_connection().query_params['id']}")
        def dynamic_key_route(self, id: int):
            return {"id": id, "message": "Cached based on query param 'id'"}
    ```
    """

    def _wraps(func: t.Callable) -> t.Callable:
        options = RouteCacheOptions(
            ttl=ttl,
            key_prefix=key_prefix,
            version=version,
            backend=backend or "default",
            make_key_callback=make_key_callback or _route_cache_make_key,
        )
        func = set_metadata(ROUTE_CACHE_OPTIONS, options)(func)
        return UseInterceptors(_CacheEllarInterceptor)(func)  # type: ignore[no-any-return]

    return _wraps
