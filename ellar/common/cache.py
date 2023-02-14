import typing as t
from functools import wraps

from ellar.cache.interface import ICacheService
from ellar.core import IExecutionContext
from ellar.core.params import ExtraEndpointArg
from ellar.helper import is_async_callable

from .decorators.extra_args import extra_args
from .routing.params import Context, Provide


class CacheDecorator:
    __slots__ = (
        "_is_async",
        "_key_prefix",
        "_version",
        "_backend",
        "_func",
        "_timeout",
        "_cache_service_arg",
        "_context_arg",
        "_make_key_callback",
    )

    def __init__(
        self,
        func: t.Callable,
        timeout: t.Union[int, float],
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
        self._timeout = timeout

        # create extra args
        self._cache_service_arg = ExtraEndpointArg(
            name="cache_service", annotation=ICacheService, default_value=Provide()  # type: ignore
        )
        self._context_arg = ExtraEndpointArg(
            name="route_context", annotation=IExecutionContext, default_value=Context()  # type: ignore
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

    def route_cache_make_key(
        self, context: IExecutionContext, key_prefix: str = ""
    ) -> str:
        """Defaults key generator for caching view"""
        connection = context.switch_to_http_connection()
        return f"{connection.get_client().url}:{key_prefix or 'view'}"

    def get_async_cache_wrapper(self) -> t.Callable:
        """Gets endpoint asynchronous wrapper function"""

        @wraps(self._func)
        async def _async_wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            cache_service: ICacheService = self._cache_service_arg.resolve(kwargs)
            context: IExecutionContext = self._context_arg.resolve(kwargs)
            key = self._make_key_callback(context, self._key_prefix or "")

            cached_value = await cache_service.get_async(
                key, self._version, backend=self._backend
            )
            if cached_value:
                return cached_value

            response = await self._func(*args, **kwargs)
            await cache_service.set_async(
                key,
                response,
                timeout=self._timeout,
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
            key = self._make_key_callback(context, self._key_prefix or "")

            cached_value = cache_service.get(key, self._version, backend=self._backend)
            if cached_value:
                return cached_value

            response = self._func(*args, **kwargs)
            cache_service.set(
                key,
                response,
                timeout=self._timeout,
                version=self._version,
                backend=self._backend,
            )
            return response

        return _wrapper


def cache(
    timeout: t.Union[float, int],
    *,
    key_prefix: str = "",
    version: str = None,
    backend: str = "default",
    make_key_callback: t.Callable[[IExecutionContext, str], str] = None,
) -> t.Callable:
    def _wraps(func: t.Callable) -> t.Callable:
        cache_decorator = CacheDecorator(
            func,
            timeout,
            key_prefix=key_prefix,
            version=version,
            backend=backend,
            make_key_callback=make_key_callback,
        )
        return cache_decorator.get_decorator_wrapper()

    return _wraps
