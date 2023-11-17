import inspect
import typing as t

from ellar.common.utils.modelfield import create_model_field
from pydantic.fields import FieldInfo, ModelField, Required
from pydantic.schema import get_annotation_from_field_info

from .. import params
from ..helpers import is_scalar_field


def get_parameter_field(
    *,
    param_default: t.Any,
    param_annotation: t.Type,
    param_name: str,
    default_field_info: t.Type[params.ParamFieldInfo] = params.ParamFieldInfo,
    ignore_default: bool = False,
    body_field_class: t.Type[FieldInfo] = params.BodyFieldInfo,
) -> ModelField:
    default_value = Required
    had_schema = False
    if param_default is not inspect.Parameter.empty and ignore_default is False:
        default_value = param_default

    if isinstance(default_value, FieldInfo):
        had_schema = True
        field_info = default_value
        default_value = field_info.default
        if (
            isinstance(field_info, params.ParamFieldInfo)
            and getattr(field_info, "in_", None) is None
        ):
            field_info.in_ = default_field_info.in_
    else:
        field_info = default_field_info(default_value)

    required = default_value == Required
    annotation: t.Any = t.Any

    if not field_info.alias and getattr(
        field_info,
        "convert_underscores",
        getattr(field_info.extra, "convert_underscores", None),
    ):
        alias = param_name.replace("_", "-")
    else:
        alias = field_info.alias or param_name

    if not param_annotation == inspect.Parameter.empty:
        annotation = param_annotation

    field = create_model_field(
        name=param_name,
        type_=get_annotation_from_field_info(annotation, field_info, param_name),
        default=None if required else default_value,
        alias=alias,
        required=required,
        field_info=field_info,
    )
    field.required = required

    if not had_schema and not is_scalar_field(field=field):
        field.field_info = body_field_class(field_info.default)

    return field
