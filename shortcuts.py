from typing import no_type_check, Callable, Any, Optional


@no_type_check
def fail_silently(func: Callable, *args: Any, **kwargs: Any) -> Optional[Any]:
    try:
        return func(*args, **kwargs)
    except (Exception,):
        pass
    return None


def normalize_path(path: str) -> str:
    while "//" in path:
        path = path.replace("//", "/")
    return path

