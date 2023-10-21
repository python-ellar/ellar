import functools
import typing as t

from pydantic import BaseConfig
from pydantic.class_validators import Validator
from pydantic.fields import FieldInfo, ModelField, UndefinedType


def create_model_field(
    name: str,
    type_: t.Type[t.Any],
    class_validators: t.Optional[t.Dict[str, Validator]] = None,
    default: t.Optional[t.Any] = None,
    required: t.Union[bool, UndefinedType] = False,
    model_config: t.Type[BaseConfig] = BaseConfig,
    field_info: t.Optional[FieldInfo] = None,
    alias: t.Optional[str] = None,
    model_field_class: t.Type[ModelField] = ModelField,
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
    except RuntimeError as e:
        raise Exception(
            f"Invalid args for response field! Hint: check that {type_} is a valid pydantic field type"
        ) from e
