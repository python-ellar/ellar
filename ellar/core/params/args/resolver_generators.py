import typing as t

from pydantic import BaseModel
from pydantic.fields import FieldInfo, ModelField

from ellar.constants import (
    MULTI_RESOLVER_FORM_GROUPED_KEY,
    MULTI_RESOLVER_KEY,
    sequence_types,
)
from ellar.core.exceptions import ImproperConfiguration

from .. import params
from ..helpers import is_scalar_field, is_scalar_sequence_field
from .factory import get_parameter_field


class BulkArgsResolverGenerator:
    __slots__ = ("param_field", "pydantic_outer_type")

    def __init__(self, pydantic_type: ModelField) -> None:
        self.pydantic_outer_type = t.cast(BaseModel, pydantic_type.outer_type_)
        self.param_field = pydantic_type

    def validate(self, field_name: str, field: ModelField) -> None:
        if not is_scalar_field(field=field) and not is_scalar_sequence_field(
            self.param_field
        ):
            raise ImproperConfiguration(
                f"field: '{field_name}' with annotation:'{field.type_}' "
                f"can't be processed. Field type should belong to {sequence_types} "
                f"or any primitive type"
            )

    def get_parameter_field(
        self,
        field_name: str,
        field: ModelField,
        field_info_attrs: t.Dict,
        body_field_class: t.Type[FieldInfo],
    ) -> t.Tuple[ModelField, params.Param]:
        field_info_type: t.Type[params.Param] = t.cast(
            t.Type[params.Param], type(self.param_field.field_info)
        )
        field_info = field_info_type(**field_info_attrs)
        model_field = get_parameter_field(
            param_default=field_info,
            param_annotation=field.outer_type_,
            default_field_info=field_info_type,
            param_name=field_info.alias or field_name,
            body_field_class=body_field_class,
        )
        return model_field, field_info

    def generate_resolvers(self, body_field_class: t.Type[FieldInfo]) -> None:
        resolvers = []
        for k, field in self.pydantic_outer_type.__fields__.items():
            self.validate(k, field)

            convert_underscores = getattr(
                self.param_field.field_info,
                "convert_underscores",
                getattr(
                    self.param_field.field_info.extra,
                    "convert_underscores",
                    None,
                ),
            )

            keys = dict(
                default=None,
                default_factory=None,
                alias=None,
                alias_priority=None,
                title=None,
                description=None,
                **field.field_info.__class__.__field_constraints__,
                **{"convert_underscores": convert_underscores}
                if convert_underscores
                else dict(),
            )

            attrs = {k: getattr(field.field_info, k, v) for k, v in keys.items()}

            model_field, field_info = self.get_parameter_field(
                k, field, attrs, body_field_class
            )
            resolver = field_info.create_resolver(model_field=model_field)
            resolvers.append(resolver)

        self.param_field.field_info.extra[MULTI_RESOLVER_KEY] = resolvers


class FormArgsResolverGenerator(BulkArgsResolverGenerator):
    def validate(self, field_name: str, field: ModelField) -> None:
        """ "Do nothing"""

    def generate_resolvers(self, body_field_class: t.Type[FieldInfo]) -> None:
        super().generate_resolvers(body_field_class=body_field_class)
        self.param_field.field_info.extra[MULTI_RESOLVER_FORM_GROUPED_KEY] = True


class PathArgsResolverGenerator(BulkArgsResolverGenerator):
    def validate(self, field_name: str, field: ModelField) -> None:
        """ "Do nothing"""
        assert is_scalar_field(
            field=field
        ), "Path params must be of one of the supported types"

    def get_parameter_field(
        self,
        field_name: str,
        field: ModelField,
        field_info_attrs: t.Dict,
        body_field_class: t.Type[FieldInfo],
    ) -> t.Tuple[ModelField, params.Param]:
        field_info = params.Path(**field_info_attrs)
        model_field = get_parameter_field(
            param_default=field_info,
            param_annotation=field.outer_type_,
            default_field_info=params.Path,
            param_name=field_info.alias or field_name,
            ignore_default=False,
        )
        return model_field, field_info
