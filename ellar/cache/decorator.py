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
    =========CONTROLLER AND ROUTE FUNCTION DECORATOR ==============

    :param ttl: the time to live
    :param key_prefix: cache key prefix
    :param version: will be used in constructing the key
    :param backend: Cache Backend to use. Default is `default`
    :param make_key_callback: Key dynamic construct.
    :return: TCallable
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
