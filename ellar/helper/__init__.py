import inspect
import re
import typing as t

class_base_function_regex: t.Pattern[t.Any] = re.compile(
    "<\\w+ ((\\w+\\.(<\\w+>)\\.)+)?(\\w+)\\.(\\w+) at \\w+>", re.IGNORECASE
)


def generate_operation_unique_id(
    *, name: str, path: str, methods: t.Sequence[str]
) -> str:
    _methods = "_".join(sorted(list(methods)))
    operation_id = name + path
    operation_id = re.sub("[^0-9a-zA-Z_]", "_", operation_id)
    operation_id = operation_id + "_" + _methods.lower()
    return operation_id


def generate_controller_operation_unique_id(
    *, path: str, methods: t.Sequence[str], versioning: t.Sequence[str]
) -> int:
    _methods = "_".join(sorted(list(methods))).lower()
    _versioning = "_".join(sorted(list(versioning))).lower()
    return hash(path + _methods + _versioning)


def get_name(endpoint: t.Union[t.Callable, t.Type, object]) -> str:
    if inspect.isfunction(endpoint) or inspect.isclass(endpoint):
        return endpoint.__name__
    return endpoint.__class__.__name__
