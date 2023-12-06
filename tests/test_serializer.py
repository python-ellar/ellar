import typing as t
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import PurePath, PurePosixPath, PureWindowsPath

import pytest
from ellar.app.context import ApplicationContext
from ellar.common.serializer.base import (
    Serializer,
    SerializerFilter,
    convert_dataclass_to_pydantic_model,
    get_dataclass_pydantic_model,
    serialize_object,
)
from ellar.pydantic import as_pydantic_validator
from ellar.testing import Test
from pydantic import BaseModel, Field, RootModel
from pydantic import dataclasses as pydantic_dataclasses


class Person:
    def __init__(self, name: str):
        self.name = name


@dataclass
class DataclassPerson:
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


ModelWithRoot = RootModel[str]


def test_convert_dataclass_to_pydantic_model():
    @dataclass
    class SomeDataClassConvert:
        name: str

    class SomeClassConvert:
        name: str

    assert getattr(SomeDataClassConvert, "__pydantic_complete__", None) is None

    pydantic_model = convert_dataclass_to_pydantic_model(SomeDataClassConvert)
    assert pydantic_model
    assert (
        getattr(pydantic_model, "__pydantic_complete__", None) is True
    ), "Converted dataclass is missing pydantic attribute"

    with pytest.raises(Exception, match="is not a dataclass"):
        convert_dataclass_to_pydantic_model(SomeClassConvert)


def test_get_dataclass_pydantic_model():
    @pydantic_dataclasses.dataclass
    class SomeDataClassConvert2:
        name: str

    assert getattr(SomeDataClassConvert2, "__pydantic_complete__", None) is True
    pydantic_model = get_dataclass_pydantic_model(SomeDataClassConvert2)
    assert pydantic_model is SomeDataClassConvert2


def test_dataclass_serializer():
    dataclass_person = DataclassPerson(name="Eadwin", first_name="Eadwin")
    assert serialize_object(dataclass_person) == {
        "name": "Eadwin",
        "first_name": "Eadwin",
        "last_name": None,
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


def test_serializer_pydantic_similar_functions():
    model = ModelWithDefault(foo="foo", bar="bar")
    dump = model.dict(exclude_none=True)
    assert dump == {"foo": "foo", "bar": "bar", "bla": "bla"}
    json_string = model.serialize_json(SerializerFilter(exclude_none=True))
    assert json_string == '{"foo":"foo","bar":"bar","bla":"bla"}'


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
    @as_pydantic_validator("__validate_schema__")
    class safe_datetime(datetime):
        @classmethod
        def __validate_schema__(cls, __input_value, *args):
            assert isinstance(__input_value, datetime)
            return __input_value

    class MyModel(BaseModel):
        dt_field: safe_datetime

    instance = MyModel(dt_field=safe_datetime.now())

    encoded_instance = serialize_object(
        instance, {safe_datetime: lambda o: o.isoformat()}
    )
    assert encoded_instance["dt_field"] == instance.dt_field.isoformat()


def test_encode_model_with_pure_path():
    class ModelWithPath(BaseModel):
        path: PurePath

        model_config = {"arbitrary_types_allowed": True}

    test_path = PurePath("/foo", "bar")
    obj = ModelWithPath(path=test_path)
    assert serialize_object(obj) == {"path": str(test_path)}
    assert serialize_object(test_path) == str(test_path)


def test_encode_model_with_pure_posix_path():
    class ModelWithPath(BaseModel):
        path: PurePosixPath
        model_config = {"arbitrary_types_allowed": True}

    obj = ModelWithPath(path=PurePosixPath("/foo", "bar"))
    assert serialize_object(obj) == {"path": "/foo/bar"}
    assert serialize_object(PurePosixPath("/foo", "bar")) == "/foo/bar"


def test_encode_model_with_path(model_with_path):
    if isinstance(model_with_path.path, PureWindowsPath):
        expected = "\\foo\\bar"
    else:
        expected = "/foo/bar"
    assert serialize_object(model_with_path) == {"path": expected}


def test_encode_root():
    model = ModelWithRoot("Foo")
    assert serialize_object(model) == "Foo"


def test_serialize_object_under_app_context():
    decoder_func_called = False

    def decoder_func(o):
        nonlocal decoder_func_called
        decoder_func_called = True
        return o.isoformat()

    class safe_datetime(datetime):
        @classmethod
        def __validate_schema__(cls, __input_value, *args):
            assert isinstance(__input_value, datetime)
            return __input_value

    tm = Test.create_test_module(
        config_module={"SERIALIZER_CUSTOM_ENCODER": {safe_datetime: decoder_func}}
    )

    with ApplicationContext.create(tm.create_application()):
        result = serialize_object(safe_datetime.fromisocalendar(2023, 45, 5))
        assert result == "2023-11-10T00:00:00"

    assert decoder_func_called is True
