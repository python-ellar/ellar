import logging
import typing as t
import weakref
from contextlib import asynccontextmanager, contextmanager
from weakref import WeakKeyDictionary, WeakValueDictionary

from .utils import ensure_target, fail_silently, get_original_target

logger = logging.getLogger("ellar")


def _try_hash(item: t.Any) -> bool:
    try:
        hash(item), weakref.ref(item)
        return True
    except TypeError:
        return False


class _Hashable:
    def __init__(self, item_id: int, item_repr: str) -> None:
        self.item_id = item_id
        self.item_repr = item_repr
        # self._item_repr = item_repr

    def __hash__(self) -> int:
        # Combine the hash values of the attributes
        attrs = self.item_id, self.item_repr
        return hash(attrs)

    def __eq__(self, other: t.Any) -> bool:
        # Check if another object is equal based on attributes
        if isinstance(other, _Hashable):
            return self.item_id == other.item_id
        return False

    def __repr__(self) -> str:
        return self.item_repr

    @classmethod
    def force_hash(cls, item: t.Any) -> t.Union[t.Any, "_Hashable"]:
        if not _try_hash(item):
            hashable = fail_silently(
                lambda: reflect._un_hashable[hash((id(item), repr(item)))]
            )
            if hashable:
                return hashable

            new_target = cls(item_id=id(item), item_repr=repr(item))
            return reflect.add_un_hashable_type(new_target)
        return item


def _get_actual_target(
    target: t.Union[t.Type, t.Callable],
) -> t.Union[t.Type, t.Callable]:
    target = get_original_target(target)
    return t.cast(
        t.Union[t.Type, t.Callable], _Hashable.force_hash(ensure_target(target))
    )


class _Reflect:
    __slots__ = ("_meta_data",)

    _un_hashable: t.Dict[int, _Hashable] = {}
    _data_type_update_callbacks: t.MutableMapping[t.Type, t.Callable] = (
        WeakValueDictionary()
    )

    def __init__(self) -> None:
        self._meta_data: t.MutableMapping[t.Union[t.Type, t.Callable], t.Dict] = (
            WeakKeyDictionary()
        )

    def add_type_update_callback(self, type_: t.Type, func: t.Callable) -> None:
        self._data_type_update_callbacks[type_] = func

    def add_un_hashable_type(self, value: _Hashable) -> _Hashable:
        self._un_hashable[hash(value)] = value
        return value

    def _default_update_callback(
        self, existing_value: t.Any, new_value: t.Any
    ) -> t.Any:
        return new_value

    def define_metadata(
        self,
        metadata_key: str,
        metadata_value: t.Any,
        target: t.Union[t.Type, t.Callable],
    ) -> t.Any:
        if target is None:
            raise Exception("`target` is not a valid type")
        # if (
        #     not isinstance(target, type)
        #     and not callable(target)
        #     and not ismethod(target)
        #     or target is None
        # ):
        #     raise Exception("`target` is not a valid type")

        target_metadata = self._get_or_create_metadata(target, create=True)
        if target_metadata is not None:
            existing = target_metadata.get(metadata_key)
            if existing is not None:
                update_callback = self._data_type_update_callbacks.get(
                    type(existing), self._default_update_callback
                )
                metadata_value = update_callback(existing, metadata_value)
            target_metadata[metadata_key] = metadata_value

    def metadata(self, metadata_key: str, metadata_value: t.Any) -> t.Any:
        def _wrapper(target: t.Union[t.Type, t.Callable]) -> t.Any:
            self.define_metadata(metadata_key, metadata_value, target)
            return target

        return _wrapper

    def has_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> bool:
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        return metadata_key in target_metadata

    def get_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> t.Optional[t.Any]:
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        value = target_metadata.get(metadata_key)
        if isinstance(value, (list, set, tuple, dict)):
            # return immutable value
            return type(value)(value)
        return value

    def get_metadata_search_safe(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> t.Any:
        _target_actual = _get_actual_target(target)
        meta = self._meta_data[_target_actual]

        value = meta[metadata_key]
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
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        return target_metadata.keys()

    def get_all_metadata(self, target: t.Union[t.Type, t.Callable]) -> t.Dict:
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}
        return type(target_metadata)(target_metadata)

    def delete_all_metadata(self, target: t.Union[t.Type, t.Callable]) -> None:
        _target = _get_actual_target(target)
        if _target in self._meta_data:
            self._meta_data.pop(_target)

    def delete_metadata(
        self, metadata_key: str, target: t.Union[t.Type, t.Callable]
    ) -> t.Any:
        _target_actual = _get_actual_target(target)
        target_metadata = self._meta_data.get(_target_actual) or {}

        if target_metadata and metadata_key in target_metadata:
            value = target_metadata.pop(metadata_key)
            if isinstance(value, (list, set, tuple, dict)):
                # return immutable value
                return type(value)(value)
            return value

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
        _meta_data: t.MutableMapping[t.Union[t.Type, t.Callable], t.Dict] = (
            WeakKeyDictionary()
        )
        for k, v in self._meta_data.items():
            _meta_data[k] = dict(v)
        return _meta_data

    @asynccontextmanager
    async def async_context(self) -> t.AsyncGenerator[None, None]:
        cached_meta_data = self._clone_meta_data()
        yield
        reflect._meta_data.clear()
        reflect._meta_data = WeakKeyDictionary(dict=cached_meta_data)

    @contextmanager
    def context(self) -> t.Generator:
        cached_meta_data = self._clone_meta_data()
        yield
        reflect._meta_data.clear()
        reflect._meta_data = WeakKeyDictionary(dict=cached_meta_data)


def _list_update(existing_value: t.Any, new_value: t.Any) -> t.Any:
    if isinstance(existing_value, (list, tuple)) and isinstance(
        new_value, (list, tuple)
    ):
        return existing_value + type(existing_value)(new_value)  # type: ignore
    return new_value


def _set_update(existing_value: t.Any, new_value: t.Any) -> t.Any:
    if isinstance(existing_value, set) and isinstance(new_value, set):
        existing_combined = list(existing_value) + list(new_value)
        return type(existing_value)(existing_combined)
    return new_value


def _dict_update(existing_value: t.Any, new_value: t.Any) -> t.Any:
    if isinstance(
        existing_value, (dict, WeakKeyDictionary, WeakValueDictionary)
    ) and isinstance(new_value, (dict, WeakKeyDictionary, WeakValueDictionary)):
        existing_value.update(new_value)
        return type(existing_value)(existing_value)
    return new_value


reflect = _Reflect()

reflect.add_type_update_callback(tuple, _list_update)
reflect.add_type_update_callback(list, _list_update)
reflect.add_type_update_callback(set, _set_update)
reflect.add_type_update_callback(dict, _dict_update)
reflect.add_type_update_callback(WeakKeyDictionary, _dict_update)
reflect.add_type_update_callback(WeakValueDictionary, _dict_update)
