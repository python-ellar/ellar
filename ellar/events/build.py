import functools
import inspect
import typing as t

from ellar.reflect import fail_silently
from ellar.threading import execute_coroutine

from .base import EventManager

build_with_context_event = EventManager()


def ensure_build_context(app_ready: bool = False) -> t.Callable:
    """
    Ensures a function runs within an active `injector_context` or defers execution until the application is bootstrapping.

    This decorator is useful for functions that need to modify the Application configuration
    or interact with the injector at execution time, handling cases where the
    build context might not yet be ready.

    If the `injector_context` is not available when the decorated function is called,
    execution is deferred until the context is established.

    Example:
    ```python
    from ellar.core import config

    @ensure_build_context
    def set_config_value(key, value):
        config[key] = value

    # These calls will run immediately if context is ready,
    # or be deferred until bootstrapping overlaps.
    set_config_value("MY_SETTINGS", 45)
    set_config_value("MY_SETTINGS_2", 100)
    ```

    :param app_ready: Determines the required state for execution.
        If ``True``, the function is executed only when the `App` instance is ready within the build context.
        If ``False`` (default), the function is executed as soon as the `injector_context` is available.
    :return: A decorator that wraps the target function.
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
