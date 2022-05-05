import typing as t

from ellar.constants import ON_APP_INIT, ON_APP_STARTED
from ellar.core.events import ApplicationEventHandler


def set_attr_key(handle: t.Callable, key: str, value: t.Any) -> None:
    setattr(handle, key, value)


def on_app_started(func: t.Optional[t.Callable] = None) -> t.Callable:
    if func and callable(func):
        set_attr_key(func, ON_APP_STARTED, ApplicationEventHandler(func))
        return func

    def decorator(func_: t.Callable) -> t.Callable:
        set_attr_key(func_, ON_APP_STARTED, ApplicationEventHandler(func_))
        return func_

    return decorator


def on_app_init(func: t.Optional[t.Callable] = None) -> t.Callable:
    if func and callable(func):
        set_attr_key(func, ON_APP_INIT, ApplicationEventHandler(func))
        return func

    def decorator(func_: t.Callable) -> t.Callable:
        set_attr_key(func_, ON_APP_INIT, ApplicationEventHandler(func_))
        return func_

    return decorator
