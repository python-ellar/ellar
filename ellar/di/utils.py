import typing as t


@t.no_type_check
def fail_silently(func: t.Callable, *args: t.Any, **kwargs: t.Any) -> t.Optional[t.Any]:
    try:
        return func(*args, **kwargs)
    except Exception:  # pragma: no cover
        pass
    return None
