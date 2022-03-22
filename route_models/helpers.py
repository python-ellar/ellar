import functools
from typing import Any, Dict, Optional, Type, Union
from pydantic import BaseConfig, BaseModel
from pydantic.class_validators import Validator
from pydantic.fields import (
    UndefinedType,
    SHAPE_SINGLETON,
    FieldInfo,
    ModelField,
)

from pydantic.schema import SHAPE_SINGLETON
from pydantic.utils import lenient_issubclass

from starletteapi.constants import sequence_types, sequence_shapes


def is_scalar_sequence_field(field: ModelField) -> bool:
    if (field.shape in sequence_shapes) and not lenient_issubclass(
        field.type_, BaseModel
    ):
        if field.sub_fields is not None:
            for sub_field in field.sub_fields:
                if not is_scalar_field(sub_field):
                    return False
        return True
    if lenient_issubclass(field.type_, sequence_types):
        return True
    return False


def is_scalar_field(field: ModelField) -> bool:
    from .params import Body, WsBody
    field_info = field.field_info
    if not (
            field.shape == SHAPE_SINGLETON
            and not lenient_issubclass(field.type_, BaseModel)
            and not lenient_issubclass(field.type_, sequence_types + (dict,))
            and not isinstance(field_info, Body)
            and not isinstance(field_info, WsBody)
    ):
        return False
    if field.sub_fields:
        if not all(is_scalar_field(f) for f in field.sub_fields):
            return False
    return True


def create_response_field(
        name: str,
        type_: Type[Any],
        class_validators: Optional[Dict[str, Validator]] = None,
        default: Optional[Any] = None,
        required: Union[bool, UndefinedType] = False,
        model_config: Type[BaseConfig] = BaseConfig,
        field_info: Optional[FieldInfo] = None,
        alias: Optional[str] = None,
        model_field_class: Type[ModelField] = ModelField
) -> ModelField:
    """
    Create a new response field. Raises if type_ is invalid.
    """
    class_validators = class_validators or {}
    field_info = field_info or FieldInfo(None)

    response_field = functools.partial(
        model_field_class,
        name=name,
        type_=type_,
        class_validators=class_validators,
        default=default,
        required=required,
        model_config=model_config,
        alias=alias,
    )

    try:
        return response_field(field_info=field_info)
    except RuntimeError:
        raise Exception(
            f"Invalid args for response field! Hint: check that {type_} is a valid pydantic field type"
        )
