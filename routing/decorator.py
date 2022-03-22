import typing as t
from .operations import OperationBase
from starletteapi.types import T


def _set_meta(meta_key: t.Any, reload: bool = False) -> t.Callable:
    def _decorator(*meta_values: t.Any) -> t.Callable:
        _meta_values = list(meta_values)

        def _operation_wrapper(operation: T) -> T:
            nonlocal _meta_values
            assert isinstance(operation, OperationBase), (
                f'invalid operation type.'
            )
            existing = operation.get_meta().get(meta_key)
            if existing:
                if isinstance(existing, (list, tuple)):
                    _meta_values.extend(existing)
                    if isinstance(existing, tuple):
                        _meta_values = tuple(_meta_values)
                elif isinstance(existing, set):
                    _meta_values.extend(existing)
                    _meta_values = set(_meta_values)

            operation.get_meta().update({meta_key: _meta_values})
            if reload:
                operation._load_model()
            return operation

        return _operation_wrapper

    return _decorator


Guards = _set_meta('route_guards')
Versions = _set_meta('route_versioning')
SetMeta = _set_meta
