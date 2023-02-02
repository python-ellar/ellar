import typing as t
from functools import partial

from ellar.constants import NOT_SET
from ellar.reflect import reflect


def set_metadata(
    meta_key: t.Any,
    meta_value: t.Optional[t.Any] = NOT_SET,
) -> t.Callable:
    if meta_value is NOT_SET:
        return partial(set_metadata, meta_key)

    def _decorator(target: t.Union[t.Callable, t.Any]) -> t.Union[t.Callable, t.Any]:
        reflect.define_metadata(meta_key, meta_value, target)
        return target

    return _decorator
