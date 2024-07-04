import typing as t

from pydantic import (
    AnyUrl,
    BaseConfig,
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    PrivateAttr,
    TypeAdapter,
    create_model,
    field_validator,
    model_validator,
)
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic.fields import FieldInfo
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import CoreSchema

from .decorator import (
    AllowTypeOfSource,
    as_pydantic_validator,
    with_info_plain_validator_function,
)
from .emails import EmailStr  # type:ignore[attr-defined]
from .encoder import ENCODERS_BY_TYPE, encoders_by_class_tuples
from .exceptions import ErrorWrapper
from .field_constraints import DefaultValues as FieldConstraintsDefaultValues
from .fields import ModelField
from .utils import (
    create_body_model,
    create_model_field,
    evaluate_forwardref,
    get_definitions,
    get_missing_field_error,
    get_schema_from_model_field,
    is_scalar_field,
    is_scalar_sequence_field,
    is_sequence_field,
    lenient_issubclass,
    model_dump,
    model_rebuild,
    regenerate_error_with_loc,
    sequence_annotation_to_type,
    sequence_types,
)

__all__ = [
    "AnyUrl",
    "with_info_plain_validator_function",
    "BaseModel",
    "BaseConfig",
    "TypeAdapter",
    "EmailStr",
    "create_model",
    "as_pydantic_validator",
    "model_dump",
    "model_rebuild",
    "get_missing_field_error",
    "get_definitions",
    "get_schema_from_model_field",
    "regenerate_error_with_loc",
    "is_scalar_field",
    "is_scalar_sequence_field",
    "evaluate_forwardref",
    "sequence_types",
    "sequence_annotation_to_type",
    "is_sequence_field",
    "create_body_model",
    "ErrorWrapper",
    "ModelField",
    "FieldInfo",
    "Field",
    "pydantic_dataclass",
    "lenient_issubclass",
    "create_model_field",
    "FieldConstraintsDefaultValues",
    "ENCODERS_BY_TYPE",
    "encoders_by_class_tuples",
    "PrivateAttr",
    "field_validator",
    "model_validator",
    "GenerateJsonSchema",
    "JsonSchemaValue",
    "CoreSchema",
    "GetCoreSchemaHandler",
    "AllowTypeOfSource",
]


def __dir__() -> t.List[str]:
    return sorted(__all__)  # pragma: no cover
