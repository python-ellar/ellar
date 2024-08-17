import functools
import typing as t

from .base import EventManager

build_with_context_event = EventManager()


def ensure_context(f: t.Callable) -> t.Callable:
    """
    Ensure function runs under injector_context
    This is useful when running a function that modifies Application config but at the time execution,
    config is not ready.

    example:
    from ellar.core import config

    @ensure_context
    def set_config_value(key, value):
        config[key] = value

    :param f:
    :return:
    """

    def _on_context(func_args: t.Tuple[t.Tuple, t.Dict], **kw: t.Any) -> t.Any:
        args, kwargs = func_args
        return f(*args, **kwargs)

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

        return f(*args, **kw)

    return _decorator
