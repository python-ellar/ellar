import typing as t

from ellar.utils.importer import import_from_string
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
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


class AllowTypeOfSource:
    def __init__(
        self,
        schema: t.Optional[t.Dict[str, t.Any]] = None,
        validator: t.Callable[..., bool] = None,
        error_message: t.Optional[t.Callable[..., str]] = None,
    ) -> None:
        self._schema = schema
        self.validator = validator
        self.error_message = error_message

    def __get_pydantic_core_schema__(
        self,
        source: t.Type[t.Any],
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        def validate(value: t.Any, *args: t.Any) -> t.Any:
            if isinstance(value, str) and len(value.split(":")) == 2:
                value = import_from_string(value)

            if (self.validator and not self.validator(source, value)) or (
                not self.validator and not isinstance(value, source)
            ):
                self._handle_error(source, value)
            return value

        return with_info_plain_validator_function(validate)

    def _handle_error(self, source: t.Any, value: t.Any) -> None:
        error_message = (
            f"Expected an instance of {source}, got an instance of {type(value)}"
            if self.error_message is None
            else self.error_message(source, value)
        )
        raise ValueError(error_message)

    def __get_pydantic_json_schema__(
        self, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:  # pragma: no cover
        return self._schema
