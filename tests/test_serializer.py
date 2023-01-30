import typing as t
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import PureWindowsPath

import pytest
from pydantic import BaseModel, Field, dataclasses as pydantic_dataclasses

from ellar.serializer import (
    DataclassSerializer,
    Serializer,
    SerializerFilter,
    convert_dataclass_to_pydantic_model,
    get_dataclass_pydantic_model,
    serialize_object,
)


class Person:
    def __init__(self, name: str):
        self.name = name


@dataclass
class DataclassPerson(DataclassSerializer):
    name: str
    first_name: str
    last_name: t.Optional[str] = None


@dataclass
class PlainDataclassPerson:
    name: str
    first_name: str
    last_name: t.Optional[str] = None


class Pet:
    def __init__(self, owner: Person, name: str):
        self.owner = owner
        self.name = name


class DictablePerson(Person):
    def __iter__(self):
        return ((k, v) for k, v in self.__dict__.items())


class DictablePet(Pet):
    def __iter__(self):
        return ((k, v) for k, v in self.__dict__.items())


class Unserializable:
    def __iter__(self):
        raise NotImplementedError()

    @property
    def __dict__(self):
        raise NotImplementedError()


class ModelWithCustomEncoder(BaseModel):
    dt_field: datetime

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.replace(
                microsecond=0, tzinfo=timezone.utc
            ).isoformat()
        }


class ModelWithCustomEncoderSubclass(ModelWithCustomEncoder):
    class Config:
        pass


class RoleEnum(Enum):
    admin = "admin"
    normal = "normal"


class ModelWithConfig(BaseModel):
    role: t.Optional[RoleEnum] = None

    class Config:
        use_enum_values = True


class ModelWithAlias(BaseModel):
    foo: str = Field(..., alias="Foo")


class ModelWithDefault(Serializer):
    foo: str = ...  # type: ignore
    bar: str = "bar"
    bla: str = "bla"
    cat: t.Optional[str] = None


class ModelWithRoot(BaseModel):
    __root__: str


def test_convert_dataclass_to_pydantic_model():
    @dataclass
    class SomeDataClassConvert:
        name: str

    class SomeClassConvert:
        name: str

    pydantic_model = convert_dataclass_to_pydantic_model(SomeDataClassConvert)
    assert pydantic_model
    assert issubclass(pydantic_model, BaseModel)

    with pytest.raises(Exception, match="is not a dataclass"):
        convert_dataclass_to_pydantic_model(SomeClassConvert)


def test_get_dataclass_pydantic_model():
    @pydantic_dataclasses.dataclass
    class SomeDataClassConvert2:
        name: str

    pydantic_model = get_dataclass_pydantic_model(SomeDataClassConvert2)
    assert pydantic_model
    assert issubclass(pydantic_model, BaseModel)


def test_dataclass_serializer():
    dataclass_person = DataclassPerson(name="Eadwin", first_name="Eadwin")
    assert serialize_object(dataclass_person) == {
        "name": "Eadwin",
        "first_name": "Eadwin",
        "last_name": None,
    }

    assert serialize_object(
        dataclass_person, serializer_filter=SerializerFilter(exclude_none=True)
    ) == {
        "name": "Eadwin",
        "first_name": "Eadwin",
    }

    plain_dataclass = PlainDataclassPerson(name="Eadwin", first_name="Eadwin")
    assert serialize_object(dataclass_person) == {
        "name": "Eadwin",
        "first_name": "Eadwin",
        "last_name": None,
    }
    assert serialize_object(
        plain_dataclass, serializer_filter=SerializerFilter(exclude_none=True)
    ) == {
        "name": "Eadwin",
        "first_name": "Eadwin",
        "last_name": None,
    }
    assert dataclass_person.get_pydantic_model()
    assert issubclass(dataclass_person.get_pydantic_model(), BaseModel)


def test_serializer_filter():
    model = ModelWithDefault(foo="foo", bar="bar")
    assert serialize_object(model) == {
        "foo": "foo",
        "bar": "bar",
        "bla": "bla",
        "cat": None,
    }

    assert serialize_object(
        model, serializer_filter=SerializerFilter(exclude_none=True)
    ) == {"foo": "foo", "bar": "bar", "bla": "bla"}
    assert serialize_object(
        model, serializer_filter=SerializerFilter(exclude_defaults=True)
    ) == {"foo": "foo"}

    assert serialize_object(
        model,
        serializer_filter=SerializerFilter(exclude_unset=True, exclude_defaults=True),
    ) == {"foo": "foo"}


def test_encode_class():
    person = Person(name="Foo")
    pet = Pet(owner=person, name="Firulais")
    assert serialize_object(pet) == {"name": "Firulais", "owner": {"name": "Foo"}}


def test_encode_dictable():
    person = DictablePerson(name="Foo")
    pet = DictablePet(owner=person, name="Firulais")
    assert serialize_object(pet) == {"name": "Firulais", "owner": {"name": "Foo"}}


def test_encode_unsupported():
    unserializable = Unserializable()
    with pytest.raises(ValueError):
        serialize_object(unserializable)


def test_encode_custom_json_encoders_model():
    model = ModelWithCustomEncoder(dt_field=datetime(2019, 1, 1, 8))
    assert serialize_object(model) == {"dt_field": "2019-01-01T08:00:00+00:00"}


def test_encode_custom_json_encoders_model_subclass():
    model = ModelWithCustomEncoderSubclass(dt_field=datetime(2019, 1, 1, 8))
    assert serialize_object(model) == {"dt_field": "2019-01-01T08:00:00+00:00"}


def test_encode_model_with_config():
    model = ModelWithConfig(role=RoleEnum.admin)
    assert serialize_object(model) == {"role": "admin"}


def test_encode_model_with_alias():
    model = ModelWithAlias(Foo="Bar")
    assert serialize_object(model) == {"Foo": "Bar"}


def test_custom_encoders():
    class safe_datetime(datetime):
        pass

    class MyModel(BaseModel):
        dt_field: safe_datetime

    instance = MyModel(dt_field=safe_datetime.now())

    encoded_instance = serialize_object(
        instance, {safe_datetime: lambda o: o.isoformat()}
    )
    assert encoded_instance["dt_field"] == instance.dt_field.isoformat()


def test_encode_model_with_path(model_with_path):
    if isinstance(model_with_path.path, PureWindowsPath):
        expected = "\\foo\\bar"
    else:
        expected = "/foo/bar"
    assert serialize_object(model_with_path) == {"path": expected}


def test_encode_root():
    model = ModelWithRoot(__root__="Foo")
    assert serialize_object(model) == "Foo"
