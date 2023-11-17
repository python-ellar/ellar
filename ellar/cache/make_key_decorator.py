import functools
import typing as t

from ellar.common.utils import is_async_callable

if t.TYPE_CHECKING:  # pragma: no cover
    from .model import BaseCacheBackend


class MakeKeyDecorator:
    __slots__ = ("_func", "_validate", "_is_async")

    def __init__(self, func: t.Callable, validate: bool = False) -> None:
        self._func = func
        self._validate = validate
        self._is_async = is_async_callable(func)

    def get_decorator(self) -> t.Callable:
        if self._is_async:
            return self.get_async_make_key_decorator()
        return self.get_make_key_decorator()

    def get_async_make_key_decorator(self) -> t.Callable:
        @functools.wraps(self._func)
        async def _wrap(
            instance: "BaseCacheBackend",
            key: str,
            *args: t.Any,
            version: t.Optional[str] = None,
            **kwargs: t.Any,
        ) -> t.Any:
            if self._validate:
                instance.validate_key(key)
            _key = instance.make_key(key, version=version)
            return await self._func(instance, _key, *args, version=version, **kwargs)

        return _wrap

    def get_make_key_decorator(self) -> t.Callable:
        @functools.wraps(self._func)
        def _wrap(
            instance: "BaseCacheBackend",
            key: str,
            *args: t.Any,
            version: t.Optional[str] = None,
            **kwargs: t.Any,
        ) -> t.Any:
            if self._validate:
                instance.validate_key(key)
            _key = instance.make_key(key, version=version)
            return self._func(instance, _key, *args, version=version, **kwargs)

        return _wrap


@t.no_type_check
def make_key_decorator(func: t.Callable) -> t.Callable[..., t.Awaitable]:
    make_key = MakeKeyDecorator(func, validate=False)
    return make_key.get_decorator()


@t.no_type_check
def make_key_decorator_and_validate(func: t.Callable) -> t.Callable[..., t.Awaitable]:
    make_key = MakeKeyDecorator(func, validate=True)
    return make_key.get_decorator()
