import typing as t
from inspect import ismethod
from weakref import WeakKeyDictionary

from ellar.compatible import AttributeDict
from ellar.constants import REFLECT_TYPE


def _get_actual_target(
    target: t.Union[t.Type, t.Callable]
) -> t.Union[t.Type, t.Callable]:
    try:
        reflect_type = target.__dict__[REFLECT_TYPE]
    except KeyError:
        setattr(target, REFLECT_TYPE, target)
        return t.cast(t.Union[t.Type, t.Callable], target)
    else:
        return t.cast(t.Union[t.Type, t.Callable], reflect_type)


class _Reflect:
    __slots__ = ("_meta_data",)

    def __init__(self) -> None:
        self._meta_data: t.MutableMapping[
            t.Union[t.Type, t.Callable], AttributeDict
        ] = WeakKeyDictionary()

    def define_metadata(
        self,
        metadata_key: str,
        metadata_value: t.Any,
        target: t.Union[t.Type, t.Callable],
        default_value: t.Any = None,
    ) -> t.Any:
        if (
            not isinstance(target, type)
            and not callable(target)
            and not ismethod(target)
        ):
            raise Exception("`target` is not a valid type")

        target_metadata = self._get_or_create_metadata(target, create=True)
        target_metadata.setdefault(metadata_key, default_value)

        _meta_values: t.Any = (
            list(metadata_value)
            if isinstance(metadata_value, (list, tuple, set))
            else [metadata_value]
        )
        existing = target_metadata.get(metadata_key)
        if existing is not None:
            if isinstance(existing, (list, tuple)):
                _meta_values.extend(existing)
                if isinstance(existing, tuple):
                    _meta_values = tuple(_meta_values)
            elif isinstance(existing, set):
                _meta_values.extend(existing)
                _meta_values = set(_meta_values)
            elif isinstance(existing, dict):
                existing = t.cast(dict, existing)
                existing.update(dict(metadata_value))
                _meta_values = dict(existing)
            else:
                # if existing item is not a Collection, And we are trying to set same key again,
                # then it has to be change to a collection
                _meta_values = [existing] + _meta_values
        else:
            _meta_values = metadata_value
        target_metadata[metadata_key] = _meta_values

    def metadata(self, metadata_key: str, metadata_value: t.Any) -> t.Any:
        def _wrapper(target: t.Union[t.Type, t.Callable]) -> t.Any:
            self.define_metadata(metadata_key, metadata_value, target)
            return target

        return _wrapper

    def has_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> bool:
        target_metadata = self._get_or_create_metadata(target) or {}
        return metadata_key in target_metadata

    def get_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> t.Optional[t.Any]:
        target_metadata = (
            self._get_or_create_metadata(target) or {}
        )
        value = target_metadata.get(metadata_key)
        if isinstance(value, (list, set, tuple, dict)):
            # return immutable value
            return type(value)(value)
        return value

    def get_metadata_keys(
        self, target: t.Union[t.Type, t.Callable]
    ) -> t.KeysView[t.Any]:
        target_metadata = (
            self._get_or_create_metadata(target) or {}
        )
        return target_metadata.keys()

    def delete_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> None:
        target_metadata = self._get_or_create_metadata(
            target
        )
        if target_metadata and metadata_key in target_metadata:
            target_metadata.pop(metadata_key)

    def _get_or_create_metadata(
        self,
        target: t.Union[t.Type, t.Callable],
        create: bool = False
    ) -> t.Optional[AttributeDict]:
        _target = _get_actual_target(target)
        if _target in self._meta_data:
            return self._meta_data[_target]

        if create:
            self._meta_data[_target] = AttributeDict()
            return self._meta_data[_target]
        return None


reflect = _Reflect()
