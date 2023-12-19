import typing as t

from ellar.common.constants import SERIALIZER_FILTER_KEY
from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import request_logger
from ellar.common.serializer import SerializerFilter
from ellar.pydantic import as_pydantic_validator, create_model_field
from ellar.reflect import reflect

from ..response_types import JSONResponse, Response
from .base import ResponseModel, ResponseModelField


@as_pydantic_validator(
    "__validate_input__",
    schema="__type_schema__",
)
class _AnySchema:
    @classmethod
    def __validate_input__(cls, __input_value: t.Any, _: t.Any) -> t.Any:
        return __input_value

    @classmethod
    def __type_schema__(cls, core_schema: t.Any, handler: t.Any) -> t.Any:
        return {"type": "object"}


DictModelField: ResponseModelField = t.cast(
    ResponseModelField,
    create_model_field(
        name="response_model",
        type_=_AnySchema,
        model_field_class=ResponseModelField,
        mode="serialization",
    ),
)


class JSONResponseModel(ResponseModel):
    response_type: t.Type[Response] = JSONResponse

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        request_logger.debug(
            f"Creating Response from returned Handler value - '{self.__class__.__name__}'"
        )
        json_response_class = t.cast(
            t.Type[JSONResponse],
            context.get_app().config.DEFAULT_JSON_CLASS or self._response_type,
        )
        response_args, headers = self.get_context_response(
            context=context, status_code=status_code
        )
        serializer_filter = reflect.get_metadata(
            SERIALIZER_FILTER_KEY, context.get_handler()
        )
        response = json_response_class(
            **response_args,
            content=self.serialize(response_obj, serializer_filter=serializer_filter),
            headers=headers,
        )
        return response

    def serialize(
        self,
        response_obj: t.Any,
        serializer_filter: t.Optional[SerializerFilter] = None,
    ) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        _response_model_field = self.get_model_field()
        assert _response_model_field, "schema must exist for JSONResponseModel"
        return _response_model_field.prep_and_serialize(
            response_obj, serializer_filter=serializer_filter
        )


class EmptyAPIResponseModel(JSONResponseModel):
    model_field_or_schema = DictModelField

    def serialize(
        self,
        response_obj: t.Any,
        serializer_filter: t.Optional[SerializerFilter] = None,
    ) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        try:
            return super().serialize(response_obj, serializer_filter)
        except Exception:
            return self._serialize_with_serializer_object(
                response_obj, serializer_filter
            )
