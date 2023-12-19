from typing import Dict, List, Union, cast

import pytest
from ellar.common.exceptions import RequestValidationError
from ellar.common.responses.models import (
    ResponseModelField,
    ResponseTypeDefinitionConverter,
)
from ellar.common.serializer import BaseSerializer
from ellar.pydantic import create_model_field
from pydantic.dataclasses import dataclass as pydantic_dataclass
from typing_extensions import get_args

from ..schema import BlogObjectDTO, NoteSchemaDC


@pydantic_dataclass
class PydanticDataClass:
    name: str
    scope: str


def test_response_type_definition_converter():
    defined_type = List[Union[BlogObjectDTO]]
    converter = ResponseTypeDefinitionConverter(defined_type)
    converted_type = converter.re_group_outer_type()
    _union = get_args(converted_type)

    for arg in get_args(_union[0]):
        assert issubclass(arg, BaseSerializer)

    defined_type = NoteSchemaDC
    converted_type = ResponseTypeDefinitionConverter(defined_type).re_group_outer_type()
    assert converted_type == NoteSchemaDC

    defined_type = BlogObjectDTO
    converted_type = ResponseTypeDefinitionConverter(defined_type).re_group_outer_type()
    assert issubclass(converted_type, BaseSerializer)

    assert converted_type(title="DTO", author="Converted to pydantic model").dict() == {
        "title": "DTO",
        "author": "Converted to pydantic model",
    }

    defined_type = Dict[str, NoteSchemaDC]
    converted_type = ResponseTypeDefinitionConverter(defined_type).re_group_outer_type()
    _, arg = get_args(converted_type)
    assert arg == NoteSchemaDC

    defined_type = List[BlogObjectDTO]
    converted_type = ResponseTypeDefinitionConverter(defined_type).re_group_outer_type()
    args = get_args(converted_type)
    assert issubclass(args[0], BaseSerializer)

    for klass in (BlogObjectDTO, NoteSchemaDC):
        assert klass in ResponseTypeDefinitionConverter._registry


def test_response_converted_types_with_response_model_field_works():
    defined_type = List[Union[NoteSchemaDC, BlogObjectDTO]]
    converted_type = ResponseTypeDefinitionConverter(defined_type).re_group_outer_type()

    model_field = cast(
        ResponseModelField,
        create_model_field(
            name="response_model",
            type_=converted_type,
            model_field_class=ResponseModelField,
            mode="serialization",
        ),
    )

    values = model_field.prep_and_serialize(
        [NoteSchemaDC(id=1, text="some text", completed=False)]
    )
    assert values == [{"id": 1, "text": "some text", "completed": False}]

    with pytest.raises(RequestValidationError):
        # invalid data
        model_field.prep_and_serialize(
            NoteSchemaDC(id=1, text="some text", completed=False)
        )

    defined_type = NoteSchemaDC
    converted_type = ResponseTypeDefinitionConverter(defined_type).re_group_outer_type()

    model_field = cast(
        ResponseModelField,
        create_model_field(
            name="response_model",
            type_=converted_type,
            model_field_class=ResponseModelField,
            mode="serialization",
        ),
    )

    values = model_field.serialize(
        NoteSchemaDC(id=1, text="some text", completed=False)
    )
    assert values == {"id": 1, "text": "some text", "completed": False}

    with pytest.raises(RequestValidationError, match="text"):
        # invalid data
        model_field.prep_and_serialize({"id": 1, "completed": False})

    defined_type = Union[NoteSchemaDC, BlogObjectDTO]
    converted_type = ResponseTypeDefinitionConverter(defined_type).re_group_outer_type()

    model_field = cast(
        ResponseModelField,
        create_model_field(
            name="response_model",
            type_=converted_type,
            model_field_class=ResponseModelField,
            mode="serialization",
        ),
    )

    values = model_field.prep_and_serialize({"title": "some title", "author": "Eadwin"})
    assert values == {"title": "some title", "author": "Eadwin"}

    with pytest.raises(RequestValidationError, match="author"):
        # invalid data
        model_field.prep_and_serialize({"title": "some title"})
