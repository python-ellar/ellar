import typing as t

from pydantic import GetJsonSchemaHandler, model_serializer
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

try:
    from pydantic_core.core_schema import (
        with_info_plain_validator_function as with_info_plain_validator_function,
    )
except ImportError:  # pragma: no cover
    from pydantic_core.core_schema import (
        general_plain_validator_function as with_info_plain_validator_function,
    )


def as_pydantic_validator(
    validate_function_name: str, schema: t.Optional[t.Union[str, dict]] = None
) -> t.Callable:
    def wrap(klass: t.Type) -> t.Type:
        def __get_pydantic_json_schema__(
            cls: t.Any, core_schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            assert isinstance(schema, (str, dict))
            if isinstance(schema, str):
                return getattr(cls, schema)(core_schema, handler)  # type:ignore[no-any-return]
            return schema

        def __get_pydantic_core_schema__(
            cls: t.Any, source: t.Type[t.Any], handler: t.Callable[[t.Any], CoreSchema]
        ) -> CoreSchema:
            return with_info_plain_validator_function(
                getattr(cls, validate_function_name)
            )

        klass.__get_pydantic_core_schema__ = classmethod(__get_pydantic_core_schema__)
        if schema:
            klass.__get_pydantic_json_schema__ = classmethod(
                __get_pydantic_json_schema__
            )
        return klass

    return wrap


def pydantic_serializable(serializing_action: t.Union[str, t.Callable]) -> t.Callable:
    def wrap(klass: t.Type) -> t.Type:
        def _model_serializing_object(self: klass) -> str:
            if callable(serializing_action):
                return serializing_action(self)

            return getattr(self, serializing_action)(self)

        klass._model_serializing_object = model_serializer(_model_serializing_object)
        return klass

    return wrap
