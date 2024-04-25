import typing as t


@t.no_type_check
def fail_silently(func: t.Callable, *args: t.Any, **kwargs: t.Any) -> t.Optional[t.Any]:
    try:
        return func(*args, **kwargs)
    except Exception as ee:  # pragma: no cover
        print(ee)
    return None
