import typing as t
from abc import ABC
from enum import Enum
from pathlib import PurePath
from types import GeneratorType

from dataclasses import is_dataclass, asdict
from pydantic import BaseModel, dataclasses as PydanticDataclasses, BaseConfig

if t.TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny


class PydanticSerializerConfig(BaseConfig):
    orm_mode = True


def serialize_object(obj: t.Any) -> t.Any:
    if isinstance(obj, BaseSerializer):
        return obj.serialize()
    if isinstance(obj, BaseModel):
        return obj.dict(by_alias=True)
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {str(k): serialize_object(v) for k, v in obj.items()}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, (str, int, float, type(None))):
        return obj
    if isinstance(obj, (list, set, frozenset, GeneratorType, tuple)):
        return [serialize_object(item) for item in obj]
    errors = []
    try:
        data = dict(obj)
    except Exception as e:
        errors.append(e)
        try:
            data = vars(obj)
        except Exception as e:
            errors.append(e)
            raise ValueError(errors)
    return serialize_object(data)


def convert_dataclass_to_pydantic_model(dataclass_type: t.Type) -> t.Type[BaseModel]:
    if is_dataclass(dataclass_type):
        # convert to dataclass
        pydantic_dataclass = PydanticDataclasses.dataclass(dataclass_type, config=PydanticSerializerConfig)
        return pydantic_dataclass.__pydantic_model__
    raise Exception(f'{dataclass_type} is not a dataclass')


class BaseSerializer:
    _include: t.Union['AbstractSetIntStr', 'MappingIntStrAny'] = None
    _exclude: t.Union['AbstractSetIntStr', 'MappingIntStrAny'] = None
    _by_alias: bool = True
    _skip_defaults: bool = None
    _exclude_unset: bool = False
    _exclude_defaults: bool = False
    _exclude_none: bool = False

    def serialize(self) -> t.Dict:
        raise NotImplementedError


class PydanticSerializerBase(BaseSerializer):
    dict: t.Callable

    def serialize(self) -> t.Dict:
        return self.dict(
            include=self._include, exclude=self._exclude, exclude_none=self._exclude_none,
            exclude_unset=self._exclude_unset, exclude_defaults=self._exclude_defaults,
            by_alias=self._by_alias
        )


class PydanticSerializer(PydanticSerializerBase, BaseModel):
    Config = PydanticSerializerConfig


class DataClassSerializer(BaseSerializer):
    _pydantic_model: t.Any = None

    @classmethod
    def get_pydantic_model(cls):
        if not cls._pydantic_model:
            cls._pydantic_model = convert_dataclass_to_pydantic_model(cls)
        return cls._pydantic_model

    def serialize(self) -> t.Dict:
        return self.get_pydantic_model().from_orm(self).dict(
            include=self._include, exclude=self._exclude, exclude_none=self._exclude_none,
            exclude_unset=self._exclude_unset, exclude_defaults=self._exclude_defaults,
            by_alias=self._by_alias
        )
