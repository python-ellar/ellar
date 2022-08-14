import inspect
import typing as t
from functools import wraps


def _executor_wrapper_async(
    cls: t.Type, func: t.Callable
) -> t.Callable[..., t.Coroutine]:
    @wraps(func)
    async def _decorator(*args: t.Any, **kwargs: t.Any) -> t.Any:
        return await func(cls, *args, **kwargs)

    return _decorator


def _executor_wrapper(cls: t.Type, func: t.Callable) -> t.Callable:
    @wraps(func)
    def _decorator(*args: t.Any, **kwargs: t.Any) -> t.Any:
        return func(cls, *args, **kwargs)

    return _decorator


def class_parameter_executor_wrapper(
    cls: t.Type, func: t.Callable
) -> t.Union[t.Callable, t.Callable[..., t.Coroutine]]:
    if inspect.iscoroutinefunction(func):
        return _executor_wrapper_async(cls, func)

    return _executor_wrapper(cls, func)
