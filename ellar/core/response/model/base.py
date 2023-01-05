import typing as t
from abc import ABC, abstractmethod
from dataclasses import is_dataclass

from pydantic import BaseModel
from pydantic.fields import ModelField

from ellar.constants import SERIALIZER_FILTER_KEY, primitive_types
from ellar.core.context import IExecutionContext
from ellar.core.converters import TypeDefinitionConverter
from ellar.core.exceptions import RequestValidationError
from ellar.helper.modelfield import create_model_field
from ellar.reflect import reflect
from ellar.serializer import (
    BaseSerializer,
    DataclassSerializer,
    Serializer,
    SerializerBase,
    SerializerFilter,
    convert_dataclass_to_pydantic_model,
    serialize_object,
)

from ..response_types import Response
from .interface import IResponseModel


def serialize_if_pydantic_object(obj: t.Any) -> t.Any:
    if isinstance(obj, BaseModel):
        return obj.dict(by_alias=True)
    elif isinstance(obj, list):
        return [serialize_if_pydantic_object(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_if_pydantic_object(v) for k, v in obj.items()}
    return obj


class ResponseResolver(t.NamedTuple):
    status_code: int
    response_model: IResponseModel
    response_object: t.Any


class ResponseModelField(ModelField):
    def validate_object(self, obj: t.Any) -> t.Any:
        values, error = self.validate(obj, {}, loc=(self.alias,))
        if error:
            _errors = list(error) if isinstance(error, list) else [error]
            raise RequestValidationError(errors=_errors)
        return values

    def serialize(
        self, obj: t.Any, serializer_filter: t.Optional[SerializerFilter] = None
    ) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        try:
            values = self.validate_object(obj=obj)
        except RequestValidationError:
            try:
                new_obj = serialize_if_pydantic_object(obj)
                values = self.validate_object(obj=new_obj)
            except RequestValidationError as req_val_ex2:
                raise req_val_ex2
        return serialize_object(values, serializer_filter=serializer_filter)


class BaseResponseModel(IResponseModel, ABC):
    __slots__ = (
        "_response_type",
        "_media_type",
        "meta",
        "_model_field",
    )

    response_type: t.Type[Response] = Response
    model_field_or_schema: t.Union[ResponseModelField, t.Any] = None
    default_description: str = "Successful Response"

    def __init__(
        self,
        description: str = None,
        model_field_or_schema: t.Union[ResponseModelField, t.Any] = None,
        **kwargs: t.Any,
    ) -> None:
        self._response_type: t.Type[Response] = t.cast(
            t.Type[Response], kwargs.get("response_type") or self.response_type
        )
        self._media_type = str(
            kwargs.get("media_type") or self._response_type.media_type
        )
        self.default_description = description or self.default_description
        self.meta = kwargs
        self._model_field = self._get_model_field_from_schema(model_field_or_schema)

    @property
    def media_type(self) -> str:
        return self._media_type

    @property
    def description(self) -> str:
        return self.default_description

    def _get_model_field_from_schema(
        self, model_field_or_schema: t.Optional[t.Union[ResponseModelField, t.Any]]
    ) -> t.Optional[ResponseModelField]:
        _model_field_or_schema: t.Optional[ResponseModelField] = (
            model_field_or_schema or self.model_field_or_schema
        )
        if not isinstance(_model_field_or_schema, ResponseModelField):
            try:
                # convert to serializable type of base `Class BaseSerializer` is possible
                new_response_schema = ResponseTypeDefinitionConverter(
                    _model_field_or_schema
                ).re_group_outer_type()
            except Exception:
                new_response_schema = _model_field_or_schema

            _model_field_or_schema = t.cast(
                ResponseModelField,
                create_model_field(
                    name="response_model",  # TODO: find a good name for the field
                    type_=new_response_schema,
                    model_field_class=ResponseModelField,
                ),
            )
        return _model_field_or_schema

    def get_model_field(self) -> t.Optional[t.Union[ResponseModelField, t.Any]]:
        return self._model_field

    @abstractmethod
    def serialize(
        self,
        response_obj: t.Any,
        serializer_filter: t.Optional[SerializerFilter] = None,
    ) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        pass

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        """Cant create custom responses, Please override this function to create a custom response"""
        response_args, headers = self.get_context_response(
            context=context, status_code=status_code
        )
        serializer_filter: t.Optional[SerializerFilter] = reflect.get_metadata(
            SERIALIZER_FILTER_KEY, context.get_handler()
        )

        response = self._response_type(
            **response_args,
            content=self.serialize(
                response_obj, serializer_filter=serializer_filter or SerializerFilter()
            ),
            headers=headers,
        )
        return response

    @classmethod
    def get_context_response(
        cls, context: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.Dict]:
        response_args = dict(kwargs)
        http_connection = context.switch_to_http_connection()
        if http_connection.has_response:
            endpoint_response = http_connection.get_response()
            response_args = dict(background=endpoint_response.background)
            if endpoint_response.status_code > 0:
                response_args["status_code"] = endpoint_response.status_code
            return response_args, dict(endpoint_response.headers)
        return response_args, {}

    def __deepcopy__(self, memodict: t.Dict = {}) -> "BaseResponseModel":
        return self.__copy__(memodict)

    def __copy__(self, memodict: t.Dict = {}) -> "BaseResponseModel":
        return self


class ResponseModel(BaseResponseModel):
    def serialize(
        self,
        response_obj: t.Any,
        serializer_filter: t.Optional[SerializerFilter] = None,
    ) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        return response_obj


class RouteResponseExecution(Exception):
    pass


class ResponseTypeDefinitionConverter(TypeDefinitionConverter):
    _registry: t.Dict[t.Any, t.Type[BaseSerializer]] = {}

    def _get_modified_type(
        self, outer_type_: t.Type
    ) -> t.Union[t.Type[BaseSerializer], t.Any]:
        if not isinstance(outer_type_, type):
            raise Exception(f"{outer_type_} is not a type")

        if issubclass(outer_type_, DataclassSerializer):
            schema_model = outer_type_.get_pydantic_model()
            cls = type(outer_type_.__name__, (schema_model, SerializerBase), {})
            return t.cast(t.Type[BaseSerializer], cls)

        if isinstance(outer_type_, type) and issubclass(outer_type_, (BaseSerializer,)):
            return outer_type_

        if issubclass(outer_type_, BaseModel):
            cls = type(outer_type_.__name__, (outer_type_, Serializer), dict())
            return t.cast(t.Type[BaseSerializer], cls)

        if is_dataclass(outer_type_):
            if hasattr(outer_type_, "__pydantic_model__"):
                schema_model = outer_type_.__pydantic_model__
                return self._get_modified_type(t.cast(type, schema_model))
            return self._get_modified_type(
                t.cast(type, convert_dataclass_to_pydantic_model(outer_type_))
            )

        if outer_type_ in primitive_types:
            return outer_type_

        attrs = {"__annotations__": getattr(outer_type_, "__annotations__", ())}
        cls = type(outer_type_.__name__, (outer_type_, Serializer), attrs)

        return t.cast(t.Type[BaseSerializer], cls)

    def get_modified_type(self, outer_type_: t.Type) -> t.Type[BaseSerializer]:
        if outer_type_ not in self._registry:
            self._registry[outer_type_] = self._get_modified_type(outer_type_)
        return self._registry[outer_type_]
