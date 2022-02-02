import functools
from typing import Any, Dict, Optional, Type, Union
from pydantic import BaseConfig
from pydantic.class_validators import Validator
from pydantic.fields import (
    FieldInfo,
    ModelField,
    UndefinedType,
)


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
