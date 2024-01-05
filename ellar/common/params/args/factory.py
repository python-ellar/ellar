import inspect
import typing as t

from ellar.pydantic import (
    FieldInfo,
    ModelField,
    create_model_field,
    is_scalar_field,
)
from ellar.pydantic import (
    types as pydantic_types,
)

from .. import params


def get_parameter_field(
    *,
    param_default: t.Any,
    param_annotation: t.Type,
    param_name: str,
    default_field_info: t.Type[params.ParamFieldInfo] = params.ParamFieldInfo,
    ignore_default: bool = False,
    body_field_class: t.Type[FieldInfo] = params.BodyFieldInfo,
) -> ModelField:
    default_value = pydantic_types.Required
    had_schema = False

    annotation: t.Any = t.Any
    if not param_annotation == inspect.Parameter.empty:
        annotation = param_annotation

    if param_default is not inspect.Parameter.empty and ignore_default is False:
        default_value = param_default

    if isinstance(default_value, FieldInfo):
        had_schema = True
        field_info = default_value
        default_value = field_info.default

        if not field_info.annotation:
            field_info.annotation = annotation
    else:
        field_info = default_field_info(default_value, annotation=annotation)

    required = default_value == pydantic_types.Required
    if not field_info.alias and getattr(
        field_info,
        "convert_underscores",
        getattr(field_info.json_schema_extra, "convert_underscores", None),
    ):
        alias = param_name.replace("_", "-")
    else:
        alias = field_info.alias or param_name

    field_info.alias = alias
    field = create_model_field(
        name=param_name,
        type_=annotation,
        default=None if required else default_value,
        alias=alias,
        # required=required,
        field_info=field_info,
    )
    # field.required = required

    if not had_schema and not is_scalar_field(field=field):
        field.field_info = body_field_class(
            default=field_info.default, annotation=annotation, alias=alias
        )

    return field
