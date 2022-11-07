import typing as t

from ellar.constants import ON_REQUEST_SHUTDOWN_KEY, ON_REQUEST_STARTUP_KEY
from ellar.core.events import EventHandler


def set_attr_key(handle: t.Callable, key: str, value: t.Any) -> None:
    setattr(handle, key, value)


def on_startup(func: t.Optional[t.Callable] = None) -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines request start up callback
    :param func:
    :return:
    """
    if func and callable(func):
        set_attr_key(func, ON_REQUEST_STARTUP_KEY, EventHandler(func))
        return func

    def decorator(func_: t.Callable) -> t.Callable:
        set_attr_key(func_, ON_REQUEST_STARTUP_KEY, EventHandler(func_))
        return func_

    return decorator


def on_shutdown(func: t.Optional[t.Callable] = None) -> t.Callable:
    """
    ========= MODULE DECORATOR ==============

    Defines request shutdown callback
    :param func:
    :return:
    """
    if func and callable(func):
        set_attr_key(func, ON_REQUEST_SHUTDOWN_KEY, EventHandler(func))
        return func

    def decorator(func_: t.Callable) -> t.Callable:
        set_attr_key(func_, ON_REQUEST_SHUTDOWN_KEY, EventHandler(func_))
        return func_

    return decorator
