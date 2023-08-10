import typing as t
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import PurePath
from types import GeneratorType

from pydantic import BaseConfig, BaseModel
from pydantic import dataclasses as PydanticDataclasses
from pydantic.json import ENCODERS_BY_TYPE

__pydantic_model__ = "__pydantic_model__"
__pydantic_config__ = "__config__"
__pydantic_root__ = "__root__"


@t.no_type_check
def get_dataclass_pydantic_model(
    dataclass_type: t.Type,
) -> t.Optional[t.Type[BaseModel]]:
    if hasattr(dataclass_type, __pydantic_model__):
        return t.cast(t.Type[BaseModel], dataclass_type.__dict__[__pydantic_model__])


class SerializerConfig(BaseConfig):
    orm_mode = True


@PydanticDataclasses.dataclass
@dataclass
class SerializerFilter:
    include: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None
    exclude: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None
    by_alias: bool = True
    skip_defaults: t.Optional[bool] = None
    exclude_unset: bool = False
    exclude_defaults: bool = False
    exclude_none: bool = False

    def dict(self) -> t.Dict:
        return asdict(self)


_serializer_filter = get_dataclass_pydantic_model(SerializerFilter)
if _serializer_filter and hasattr(_serializer_filter, "update_forward_refs"):
    _serializer_filter.update_forward_refs()


class BaseSerializer:
    _filter: SerializerFilter = SerializerFilter()

    def serialize(
        self, serializer_filter: t.Optional[SerializerFilter] = None
    ) -> t.Dict:  # pragma: no cover
        raise NotImplementedError


class SerializerBase(BaseSerializer):
    dict: t.Callable

    def serialize(
        self, serializer_filter: t.Optional[SerializerFilter] = None
    ) -> t.Dict:
        _filter = serializer_filter or self._filter
        return t.cast(
            dict,
            self.dict(**_filter.dict()),
        )


class Serializer(SerializerBase, BaseModel):
    Config = SerializerConfig


class DataclassSerializer(BaseSerializer):
    _pydantic_model: t.Optional[t.Type[BaseModel]] = None
    __config__: t.Type[BaseConfig] = SerializerConfig

    @classmethod
    def get_pydantic_model(cls) -> t.Type[BaseModel]:
        if not cls._pydantic_model:
            cls._pydantic_model = convert_dataclass_to_pydantic_model(cls)
        return cls._pydantic_model

    def serialize(
        self, serializer_filter: t.Optional[SerializerFilter] = None
    ) -> t.Dict:
        _filter = serializer_filter or self._filter
        return t.cast(
            dict,
            self.get_pydantic_model().from_orm(self).dict(**_filter.dict()),
        )


def convert_dataclass_to_pydantic_model(dataclass_type: t.Type) -> t.Type[BaseModel]:
    if is_dataclass(dataclass_type):
        # convert to dataclass
        pydantic_dataclass = PydanticDataclasses.dataclass(
            dataclass_type,
            config=getattr(dataclass_type, __pydantic_config__, SerializerConfig),
        )
        return pydantic_dataclass.__pydantic_model__
    raise Exception(f"{dataclass_type} is not a dataclass")


def serialize_object(
    obj: t.Any,
    encoders: t.Dict[t.Any, t.Callable[[t.Any], t.Any]] = ENCODERS_BY_TYPE,
    serializer_filter: t.Optional[SerializerFilter] = None,
) -> t.Any:
    if isinstance(obj, (BaseModel, BaseSerializer)):
        __config__ = getattr(obj, __pydantic_config__, {})
        json_encoders = getattr(__config__, "json_encoders", {})

        _encoders = dict(encoders)
        if json_encoders:
            _encoders.update(json_encoders)

        obj_dict = (
            obj.serialize(serializer_filter)
            if isinstance(obj, BaseSerializer)
            else obj.dict(**(serializer_filter or SerializerFilter()).dict())
        )

        if __pydantic_root__ in obj_dict:
            obj_dict = obj_dict[__pydantic_root__]

        return serialize_object(obj_dict, _encoders)
    if is_dataclass(obj):
        return serialize_object(asdict(obj), encoders, serializer_filter)
    if isinstance(obj, dict):
        return {
            str(k): serialize_object(v, encoders, serializer_filter)
            for k, v in obj.items()
        }
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, (str, int, float, type(None))):
        return obj
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [serialize_object(item, encoders, serializer_filter) for item in obj]

    if type(obj) in encoders:
        return encoders[type(obj)](obj)

    errors = []
    try:
        data = dict(obj)
    except Exception as e1:
        errors.append(e1)
        try:
            data = vars(obj)
        except Exception as e2:
            errors.append(e2)
            raise ValueError(errors) from e2
    return serialize_object(data, encoders, serializer_filter)
