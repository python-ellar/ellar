import functools
import inspect
import typing as t

from ellar.reflect import fail_silently
from ellar.threading import execute_coroutine

from .base import EventManager

build_with_context_event = EventManager()


def ensure_build_context(app_ready: bool = False) -> t.Callable:
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

    :param app_ready: Determine when a decorated function is called.
    True value executes decorated function when App is ready in build context chain
    False value executes decorated function when injector_context is ready
    :return:
    """

    async def _on_context(
        f: t.Callable, func_args: t.Tuple[t.Tuple, t.Dict], **kw: t.Any
    ) -> t.Any:
        args, kwargs = func_args
        res = f(*args, **kwargs)

        if isinstance(res, t.Coroutine):
            await res

    def _decorator(f: t.Callable) -> t.Callable:
        is_coroutine = inspect.iscoroutinefunction(f)

        def _wrap(*args: t.Any, **kw: t.Any) -> t.Any:
            from ellar.core.execution_context.injector import (  # type:ignore[attr-defined]
                _injector_context_var,
                empty,
            )

            def _reg() -> t.Any:
                _func_args = (args, kw)
                return build_with_context_event.connect(
                    functools.partial(_on_context, f, _func_args)
                )

            if _injector_context_var.get() is empty:
                # Defer till when injector_context is ready
                return _reg()

            app = fail_silently(_injector_context_var.get().get, "App")
            if _injector_context_var.get() is not empty and app_ready and app is None:
                # Defer till when the app is ready
                return _reg()

            res = f(*args, **kw)

            if is_coroutine:
                return execute_coroutine(res)

            return res

        return _wrap

    return _decorator
