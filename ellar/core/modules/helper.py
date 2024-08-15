import inspect
import typing as t
from functools import wraps

from ellar.core import current_injector


def _executor_wrapper_async(
    cls: t.Type, func: t.Callable
) -> t.Callable[..., t.Coroutine]:
    @wraps(func)
    async def _decorator(*args: t.Any, **kwargs: t.Any) -> t.Any:
        instance = current_injector.get(cls)
        return await func(instance, *args, **kwargs)

    return _decorator


def _executor_wrapper(cls: t.Type, func: t.Callable) -> t.Callable:
    @wraps(func)
    def _decorator(*args: t.Any, **kwargs: t.Any) -> t.Any:
        instance = current_injector.get(cls)
        return func(instance, *args, **kwargs)

    return _decorator


def module_callable_factory(
    func: t.Callable, cls: t.Type
) -> t.Union[t.Callable, t.Callable[..., t.Coroutine]]:
    if inspect.iscoroutinefunction(func):
        return _executor_wrapper_async(cls, func)

    return _executor_wrapper(cls, func)
