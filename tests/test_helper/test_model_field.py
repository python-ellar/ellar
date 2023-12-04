import pytest
from ellar.common.pydantic import ModelField, create_model_field
from ellar.common.responses.models import ResponseModelField
from pydantic import PydanticUndefinedAnnotation


def test_create_model_field_works():
    response_model = create_model_field(
        name="response_model",
        type_=dict,
        model_field_class=ResponseModelField,
    )
    assert isinstance(response_model, ModelField)
    assert response_model.type_ == dict
    assert response_model.type_ == dict


def test_create_model_field_fails():
    with pytest.raises(
        PydanticUndefinedAnnotation,
    ):
        create_model_field(
            name="response_model",
            type_="whatever",
        )
