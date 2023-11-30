import typing as t
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import PurePath
from types import GeneratorType

from ellar.common.pydantic import (
    ENCODERS_BY_TYPE,
    BaseConfig,
    BaseModel,
    TypeAdapter,
    model_dump,
    pydantic_dataclass,
)

__pydantic_model__ = "__pydantic_core_schema__"
__pydantic_config__ = "__pydantic_config__"
__pydantic_root__ = "__root__"
__skip_filter__ = "__skip_filter__"


@t.no_type_check
def get_dataclass_pydantic_model(
    dataclass_type: t.Type,
) -> t.Optional[t.Type[BaseModel]]:
    if hasattr(dataclass_type, __pydantic_model__):
        return t.cast(t.Type[BaseModel], dataclass_type)


class SerializerConfig(BaseConfig):
    from_attributes = True


@pydantic_dataclass
@dataclass
class SerializerFilter:
    include: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None
    exclude: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None
    by_alias: bool = True
    exclude_unset: bool = False
    exclude_defaults: bool = False
    exclude_none: bool = False

    def __post_init__(self) -> None:
        self._type_adapter: TypeAdapter[t.Any] = TypeAdapter(self.__class__)

    def dict(self) -> t.Dict:
        return self._type_adapter.dump_python(  # type:ignore[no-any-return]
            self,
            mode="json",
        )


default_serializer_filter = SerializerFilter()


class BaseSerializer:
    _filter: SerializerFilter

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        if __skip_filter__ in kwargs:
            return

        if not hasattr(cls, "_filter"):
            cls._filter = default_serializer_filter

    def serialize(
        self, serializer_filter: t.Optional[SerializerFilter] = None
    ) -> t.Dict:  # pragma: no cover
        raise NotImplementedError


class SerializerBase(BaseSerializer, __skip_filter__=True):
    def serialize(
        self, serializer_filter: t.Optional[SerializerFilter] = None
    ) -> t.Dict:
        _filter = serializer_filter or self._filter
        return t.cast(
            dict,
            self.model_dump(**_filter.dict()),  # type:ignore[attr-defined]
        )


class Serializer(SerializerBase, BaseModel, __skip_filter__=True):
    model_config = {"from_attributes": True}

    def dict(self, *args: t.Any, **kwargs: t.Any) -> t.Dict:
        return self.model_dump(*args, **kwargs)


class DataclassSerializer(BaseSerializer, __skip_filter__=True):
    _pydantic_model: t.Optional[t.Type[BaseModel]] = None
    __pydantic_config__: t.Type[BaseConfig] = SerializerConfig

    @classmethod
    def get_pydantic_model(cls) -> t.Type[BaseModel]:
        if not cls._pydantic_model:
            cls._pydantic_model = convert_dataclass_to_pydantic_model(cls)
        return cls._pydantic_model

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: t.Any, handler: t.Any) -> t.Any:
        schema = cls.get_pydantic_model()
        return TypeAdapter(schema).json_schema()

    def serialize(
        self, serializer_filter: t.Optional[SerializerFilter] = None
    ) -> t.Dict:
        _filter = serializer_filter or self._filter
        return t.cast(
            dict,
            self.get_pydantic_model().model_validate(self).model_dump(**_filter.dict()),
        )


def convert_dataclass_to_pydantic_model(dataclass_type: t.Type) -> t.Type[BaseModel]:
    if is_dataclass(dataclass_type):
        # convert to dataclass
        decorator = pydantic_dataclass(
            config=getattr(dataclass_type, __pydantic_config__, SerializerConfig),
        )
        pydantic_dataclass_cls = decorator(t.cast(t.Any, dataclass_type))
        # sa = {item: getattr(pydantic_dataclass, item) for item in dir(pydantic_dataclass)}
        return t.cast(t.Type[BaseModel], pydantic_dataclass_cls)
    raise Exception(f"{dataclass_type} is not a dataclass")


def serialize_object(
    obj: t.Any,
    encoders: t.Dict[t.Any, t.Callable[[t.Any], t.Any]] = ENCODERS_BY_TYPE,
    serializer_filter: t.Optional[SerializerFilter] = None,
) -> t.Any:
    if isinstance(obj, (BaseModel, BaseSerializer)):
        if isinstance(obj, BaseSerializer):
            obj_dict = obj.serialize(serializer_filter)
        else:
            obj_dict = model_dump(
                obj, mode="json", **(serializer_filter or SerializerFilter()).dict()
            )

        if __pydantic_root__ in obj_dict:
            obj_dict = obj_dict[__pydantic_root__]

        return serialize_object(obj_dict, encoders)
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

    encoder = encoders.get(type(obj))
    if encoder:
        return encoder(obj)

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
