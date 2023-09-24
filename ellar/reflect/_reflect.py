import logging
import typing as t
from contextlib import contextmanager
from inspect import ismethod
from weakref import WeakKeyDictionary

from .constants import REFLECT_TYPE
from .contextmanager_fix import asynccontextmanager

logger = logging.getLogger("ellar")


def _get_actual_target(
    target: t.Union[t.Type, t.Callable]
) -> t.Union[t.Type, t.Callable]:
    try:
        reflect_type = target.__dict__[REFLECT_TYPE]
    except KeyError:
        try:
            setattr(target, REFLECT_TYPE, target)
        except Exception as ex:  # pragma: no cover
            logger.debug(f"Setting REFLECT_TYPE failed. \nError Message: {ex}")
        return target
    else:
        return t.cast(t.Union[t.Type, t.Callable], reflect_type)


class _Reflect:
    __slots__ = ("_meta_data",)

    def __init__(self) -> None:
        self._meta_data: t.MutableMapping[
            t.Union[t.Type, t.Callable], t.Dict
        ] = WeakKeyDictionary()

    def define_metadata(
        self,
        metadata_key: str,
        metadata_value: t.Any,
        target: t.Union[t.Type, t.Callable],
    ) -> t.Any:
        if (
            not isinstance(target, type)
            and not callable(target)
            and not ismethod(target)
            or target is None
        ):
            raise Exception("`target` is not a valid type")

        target_metadata = self._get_or_create_metadata(target, create=True)
        if target_metadata is not None:
            existing = target_metadata.get(metadata_key)
            if existing is not None:
                if isinstance(existing, (list, tuple)) and isinstance(
                    metadata_value, (list, tuple)
                ):
                    metadata_value = existing + type(existing)(metadata_value)  # type: ignore
                elif isinstance(existing, set) and isinstance(metadata_value, set):
                    existing_combined = list(existing) + list(metadata_value)
                    metadata_value = type(existing)(existing_combined)
                elif isinstance(existing, dict) and isinstance(metadata_value, dict):
                    existing.update(dict(metadata_value))
                    metadata_value = type(existing)(existing)
            target_metadata[metadata_key] = metadata_value

    def metadata(self, metadata_key: str, metadata_value: t.Any) -> t.Any:
        def _wrapper(target: t.Union[t.Type, t.Callable]) -> t.Any:
            self.define_metadata(metadata_key, metadata_value, target)
            return target

        return _wrapper

    def has_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> bool:
        target_metadata: t.Dict = self._get_or_create_metadata(target) or {}
        return metadata_key in target_metadata

    def get_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> t.Optional[t.Any]:
        target_metadata: t.Dict = self._get_or_create_metadata(target) or {}
        value = target_metadata.get(metadata_key)
        if isinstance(value, (list, set, tuple, dict)):
            # return immutable value
            return type(value)(value)
        return value

    def get_metadata_or_raise_exception(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> t.Any:
        value = self.get_metadata(metadata_key=metadata_key, target=target)
        if value is not None:
            return value
        raise Exception("MetaData Key not Found")

    def get_metadata_keys(
        self, target: t.Union[t.Type, t.Callable]
    ) -> t.KeysView[t.Any]:
        target_metadata: t.Dict = self._get_or_create_metadata(target) or {}
        return target_metadata.keys()

    def delete_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> None:
        target_metadata = self._get_or_create_metadata(target)
        if target_metadata and metadata_key in target_metadata:
            target_metadata.pop(metadata_key)

    def _get_or_create_metadata(
        self, target: t.Union[t.Type, t.Callable], create: bool = False
    ) -> t.Optional[t.Dict]:
        _target = _get_actual_target(target)
        if _target in self._meta_data:
            return self._meta_data[_target]

        if create:
            self._meta_data[_target] = {}
            return self._meta_data[_target]
        return None

    def _clone_meta_data(
        self,
    ) -> t.MutableMapping[t.Union[t.Type, t.Callable], t.Dict]:
        _meta_data: t.MutableMapping[
            t.Union[t.Type, t.Callable], t.Dict
        ] = WeakKeyDictionary()
        for k, v in self._meta_data.items():
            _meta_data[k] = dict(v)
        return _meta_data

    @asynccontextmanager
    async def async_context(self) -> t.AsyncGenerator[None, None]:
        cached_meta_data = self._meta_data
        try:
            self._meta_data = self._clone_meta_data()
            yield
        finally:
            self._meta_data.clear()
            self._meta_data = cached_meta_data

    @contextmanager
    def context(
        self,
    ) -> t.Generator:
        cached_meta_data = self._meta_data
        try:
            self._meta_data = self._clone_meta_data()
            yield
        finally:
            self._meta_data.clear()
            self._meta_data = cached_meta_data


reflect = _Reflect()
