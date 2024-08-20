import functools
import inspect
import typing as t

from ellar.threading import execute_coroutine

from .base import EventManager

build_with_context_event = EventManager()


def ensure_build_context(f: t.Callable) -> t.Callable:
    """
    Ensure function runs under injector_context or when injector_context when bootstrapping application
    This is useful when running a function that modifies Application config but at the time execution,
    build_context is not available is not ready.

    example:
    from ellar.core import config

    @ensure_build_context
    def set_config_value(key, value):
        config[key] = value

    set_config_value("MY_SETTINGS", 45)
    set_config_value("MY_SETTINGS_2", 100)

    :param f:
    :return:
    """
    is_coroutine = inspect.iscoroutinefunction(f)

    async def _on_context(func_args: t.Tuple[t.Tuple, t.Dict], **kw: t.Any) -> t.Any:
        args, kwargs = func_args
        res = f(*args, **kwargs)

        if isinstance(res, t.Coroutine):
            await res

    def _decorator(*args: t.Any, **kw: t.Any) -> t.Any:
        from ellar.core.execution_context.injector import (  # type:ignore[attr-defined]
            _injector_context_var,
            empty,
        )

        if _injector_context_var.get() is empty:
            _func_args = (args, kw)
            return build_with_context_event.connect(
                functools.partial(_on_context, _func_args)
            )

        res = f(*args, **kw)

        if is_coroutine:
            return execute_coroutine(res)

        return res

    return _decorator
