import logging
import typing as t

logger = logging.getLogger("ellar")


@t.no_type_check
def fail_silently(func: t.Callable, *args: t.Any, **kwargs: t.Any) -> t.Optional[t.Any]:
    try:
        return func(*args, **kwargs)
    except Exception as ex:  # pragma: no cover
        logger.debug(
            f"Calling {func} with args: {args} kw: {kwargs} failed\nException: {ex}"
        )
    return None
