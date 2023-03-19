import typing as t
import uuid
from functools import wraps

from ellar.cache.interface import ICacheService
from ellar.common import Context, Provide, extra_args
from ellar.core import ExecutionContext, IExecutionContext
from ellar.core.params import ExtraEndpointArg
from ellar.helper import is_async_callable


class _CacheDecorator:
    __slots__ = (
        "_is_async",
        "_key_prefix",
        "_version",
        "_backend",
        "_func",
        "_ttl",
        "_cache_service_arg",
        "_context_arg",
        "_make_key_callback",
    )

    def __init__(
        self,
        func: t.Callable,
        ttl: t.Union[int, float],
        *,
        key_prefix: str = "",
        version: str = None,
        backend: str = "default",
        make_key_callback: t.Callable[[IExecutionContext, str], str] = None,
    ) -> None:
        self._is_async = is_async_callable(func)
        self._key_prefix = key_prefix
        self._version = version
        self._backend = backend
        self._func = func
        self._ttl = ttl

        # create extra args
        self._cache_service_arg = ExtraEndpointArg(
            name=f"cache_service_{uuid.uuid4().hex[:4]}", annotation=ICacheService, default_value=Provide()  # type: ignore
        )
        self._context_arg = ExtraEndpointArg(
            name=f"route_context_{uuid.uuid4().hex[:4]}", annotation=IExecutionContext, default_value=Context()  # type: ignore
        )
        # apply extra_args to endpoint
        extra_args(self._cache_service_arg, self._context_arg)(func)
        self._make_key_callback: t.Callable[[IExecutionContext, str], str] = (
            make_key_callback or self.route_cache_make_key
        )

    def get_decorator_wrapper(self) -> t.Callable:
        if self._is_async:
            return self.get_async_cache_wrapper()
        return self.get_cache_wrapper()

    def route_cache_make_key(self, context: IExecutionContext, key_prefix: str) -> str:
        """Defaults key generator for caching view"""
        connection = context.switch_to_http_connection()
        return f"{connection.get_client().url}:{key_prefix or 'view'}"

    def get_async_cache_wrapper(self) -> t.Callable:
        """Gets endpoint asynchronous wrapper function"""

        @wraps(self._func)
        async def _async_wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            cache_service: ICacheService = self._cache_service_arg.resolve(kwargs)
            context: IExecutionContext = self._context_arg.resolve(kwargs)

            backend = cache_service.get_backend(backend=self._backend)
            key = self._make_key_callback(
                context, self._key_prefix or backend.key_prefix
            )

            cached_value = await cache_service.get_async(
                key, self._version, backend=self._backend
            )
            if cached_value:
                return cached_value

            response = await self._func(*args, **kwargs)
            await cache_service.set_async(
                key,
                response,
                ttl=self._ttl,
                version=self._version,
                backend=self._backend,
            )
            return response

        return _async_wrapper

    def get_cache_wrapper(self) -> t.Callable:
        """Gets endpoint synchronous wrapper function"""

        @wraps(self._func)
        def _wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            cache_service: ICacheService = self._cache_service_arg.resolve(kwargs)
            context: IExecutionContext = self._context_arg.resolve(kwargs)

            backend = cache_service.get_backend(backend=self._backend)
            key = self._make_key_callback(
                context, self._key_prefix or backend.key_prefix
            )

            cached_value = cache_service.get(key, self._version, backend=self._backend)
            if cached_value:
                return cached_value

            response = self._func(*args, **kwargs)
            cache_service.set(
                key,
                response,
                ttl=self._ttl,
                version=self._version,
                backend=self._backend,
            )
            return response

        return _wrapper


def cache(
    ttl: t.Union[float, int],
    *,
    key_prefix: str = "",
    version: str = None,
    backend: str = "default",
    make_key_callback: t.Callable[
        [t.Union[ExecutionContext, IExecutionContext], str], str
    ] = None,
) -> t.Callable:
    """

    :param ttl: the time to live
    :param key_prefix: cache key prefix
    :param version: will be used in constructing the key
    :param backend: Cache Backend to use. Default is `default`
    :param make_key_callback: Key dynamic construct.
    :return: TCallable
    """

    def _wraps(func: t.Callable) -> t.Callable:
        cache_decorator = _CacheDecorator(
            func,
            ttl,
            key_prefix=key_prefix,
            version=version,
            backend=backend,
            make_key_callback=make_key_callback,
        )
        return cache_decorator.get_decorator_wrapper()

    return _wraps
