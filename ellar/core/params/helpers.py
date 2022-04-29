from pydantic import BaseModel
from pydantic.fields import SHAPE_SINGLETON, ModelField
from pydantic.utils import lenient_issubclass

from ellar.constants import sequence_shapes, sequence_types


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
