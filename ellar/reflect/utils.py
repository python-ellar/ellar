import functools
import inspect
import logging
import typing as t

logger = logging.getLogger("ellar")


def ensure_target(target: t.Union[t.Type, t.Callable]) -> t.Union[t.Type, t.Callable]:
    res = target
    if inspect.ismethod(res):
        res = target.__func__
    return res


def is_decorated_with_partial(func_or_class: t.Any) -> bool:
    return isinstance(func_or_class, functools.partial)


def is_decorated_with_wraps(func_or_class: t.Any) -> bool:
    return hasattr(func_or_class, "__wrapped__")


def get_original_target(func_or_class: t.Any) -> t.Any:
    while True:
        if is_decorated_with_partial(func_or_class):
            func_or_class = func_or_class.func
        elif is_decorated_with_wraps(func_or_class):
            func_or_class = func_or_class.__wrapped__
        else:
            return func_or_class


def transfer_metadata(
    old_target: t.Any, new_target: t.Any, clean_up: bool = False
) -> None:
    from ._reflect import reflect

    meta = reflect.get_all_metadata(old_target)
    for k, v in meta.items():
        reflect.define_metadata(k, v, new_target)

    if clean_up:
        reflect.delete_all_metadata(old_target)


@t.no_type_check
def fail_silently(func: t.Callable, *args: t.Any, **kwargs: t.Any) -> t.Optional[t.Any]:
    try:
        return func(*args, **kwargs)
    except Exception as ex:  # pragma: no cover
        logger.debug(
            f"Calling {func} with args: {args} kw: {kwargs} failed\nException: {ex}"
        )
    return None
