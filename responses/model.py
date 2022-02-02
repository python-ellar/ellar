from typing import Union, Dict, List, Sequence, cast, Type, Tuple, Any

from dataclasses import is_dataclass
from pydantic import BaseModel
from pydantic.fields import ModelField
from pydantic.schema import model_schema

from .responses import Response
from starletteapi.context import ExecutionContext
from starletteapi.converters import TypeDefinitionConverter
from starletteapi.exceptions import RequestValidationError
from starletteapi.routing.route_models.helpers import create_response_field
from starletteapi.responses.serializer import BaseSerializer, DataClassSerializer, PydanticSerializerBase, \
    PydanticSerializer, convert_dataclass_to_pydantic_model, serialize_object


class ResponseModel:
    def __init__(self, response_type: Any) -> None:
        self.response_type = response_type
        self.media_type = getattr(response_type or {}, 'media_type', None)

    def serialize(self, response_obj: Any) -> Union[List[Dict], Dict]:
        return response_obj

    def get_schema(self, ref_prefix: str = '#/components/schemas/') -> Dict[str, Any]:
        return dict()


class APIResponseModel(ResponseModel):
    def __init__(self, response_model_field: 'ResponseModelField') -> None:
        super().__init__(response_type=None)
        self.response_model_field = response_model_field
        self.media_type = 'application/json'

    def serialize(self, response_obj: Any) -> Union[List[Dict], Dict]:
        return self.response_model_field.serialize(response_obj)

    def get_schema(self, ref_prefix: str = '#/components/schemas/') -> Dict[str, Any]:
        return model_schema(self.response_model_field, by_alias=True, ref_prefix=ref_prefix)


class EmptyAPIResponseModel(ResponseModel):
    def __init__(self) -> None:
        super().__init__(response_type={})

    def serialize(self, response_obj: Any) -> Union[List[Dict], Dict]:
        try:
            # try an serialize object
            return serialize_object(response_obj)
        except Exception:
            """Failed to auto serialize object"""
        return response_obj

    def get_schema(self, ref_prefix: str = '#/components/schemas/') -> Dict[str, Any]:
        return dict()


class ResponseModelField(ModelField):
    def validate_object(self, obj: Any) -> Any:
        values, errors = self.validate(obj, {}, loc=(self.alias,))
        if errors:
            raise RequestValidationError(errors=errors)
        return values

    def serialize(self, obj) -> Union[List[Dict], Dict]:
        values = self.validate_object(obj=obj)
        if isinstance(values, list):
            values = cast(Sequence[BaseSerializer], values)
            return [item.serialize() for item in values]
        values = cast(BaseSerializer, values)
        return values.serialize()


class RouteResponseExecution(Exception):
    pass


class ResponseTypeDefinitionConverter(TypeDefinitionConverter):
    def get_modified_type(self, outer_type_: Type) -> Type[BaseSerializer]:
        if not isinstance(outer_type_, type):
            raise Exception(f"{outer_type_} is not a type")

        if issubclass(outer_type_, DataClassSerializer):
            schema_model = outer_type_.get_pydantic_model()
            cls = type(outer_type_.__name__, (schema_model, PydanticSerializerBase, BaseSerializer), {})
            return cast(Type[BaseSerializer], cls)

        if isinstance(outer_type_, type) and issubclass(outer_type_, (BaseSerializer,)):
            return outer_type_

        if issubclass(outer_type_, BaseModel):
            if not outer_type_.Config.orm_mode:
                outer_type_.Config.orm_mode = True
            cls = type(outer_type_.__name__, (outer_type_, PydanticSerializer), dict())
            return cast(Type[BaseSerializer], cls)

        if is_dataclass(outer_type_):
            if hasattr(outer_type_, '__pydantic_model__'):
                schema_model = outer_type_.__pydantic_model__
                return self.get_modified_type(cast(type, schema_model))
            return self.get_modified_type(cast(type, convert_dataclass_to_pydantic_model(outer_type_)))

        cls = type(outer_type_.__name__, (outer_type_, PydanticSerializer), dict())
        return cast(Type[BaseSerializer], cls)


class RouteResponseModel:
    def __init__(self, route_responses: Union[Type, Dict[int, Type]]) -> None:
        self.models: Dict[int, ResponseModel] = {}
        self.convert_route_responses_to_response_models(route_responses)

    def convert_route_responses_to_response_models(self, route_responses: Union[Type, Dict[int, Type]]) -> None:
        _route_responses = self.get_route_responses_as_dict(route_responses)
        for status_code, response_schema in _route_responses.items():
            assert isinstance(status_code, int) or status_code == Ellipsis, 'status_code must be a number'

            if isinstance(response_schema, type) and issubclass(response_schema, Response):
                self.models[status_code] = ResponseModel(response_schema)
                continue

            if isinstance(response_schema, ResponseModel):
                self.models[status_code] = response_schema
                continue

            new_response_schema = ResponseTypeDefinitionConverter(response_schema).re_group_outer_type()
            model_field = create_response_field(
                name="response_model", type_=new_response_schema, model_field_class=ResponseModelField
            )
            self.models[status_code] = APIResponseModel(cast(ResponseModelField, model_field))

    def resolve_content(
            self, endpoint_response_content: Union[Any, Tuple[int, Any]]
    ) -> Union[Tuple[int, Union[Dict, List[Dict]]], Dict, List[dict]]:
        status_code: int = 200
        response_obj = endpoint_response_content
        response_model = None

        if len(self.models) == 1:
            status_code = list(self.models.keys())[0]

        if isinstance(response_obj, tuple) and len(response_obj) == 2:
            status_code, response_obj = endpoint_response_content

        if status_code in self.models:
            response_model = self.models[status_code]
        elif Ellipsis in self.models:
            response_model = self.models[Ellipsis]
        else:
            RouteResponseExecution(
                f"No response Schema with status_code={status_code} in response {self.models.keys()}"
            )

        if response_model:
            return status_code, response_model.serialize(response_obj)
        return status_code, endpoint_response_content

    def process_response(
            self, ctx: ExecutionContext, response_obj: Union[Any, Tuple[int, Any]]
    ) -> Response:
        if isinstance(response_obj, Response):
            return response_obj

        json_response_class = ctx.get_app().config.DEFAULT_JSON_CLASS

        if ctx.has_response:
            endpoint_response = ctx.get_response()
            response_args = dict(
                background=endpoint_response.background, status_code=endpoint_response.status_code
            )
            if not isinstance(response_obj, tuple):
                response_obj = (endpoint_response.status_code, response_obj)
            _, content = self.resolve_content(response_obj)
            response = json_response_class(content=content, **response_args)
            response.headers.raw.extend(endpoint_response.headers.raw)
            return response

        status_code, content = self.resolve_content(response_obj)
        response = json_response_class(content=content, status_code=status_code)
        return response

    @classmethod
    def get_route_responses_as_dict(cls, route_responses: Union[Type, Dict[int, Type]]) -> Dict[int, Type]:
        _route_responses = {}

        if not isinstance(route_responses, (Sequence, dict)):
            if isinstance(route_responses, type) and issubclass(route_responses, Response):
                if route_responses.media_type and route_responses.media_type.lower() == 'application/json':
                    raise RouteResponseExecution('JSONResponse type is not required.')
                _route_responses[200] = route_responses
            return _route_responses

        if not isinstance(route_responses, dict):
            raise RouteResponseExecution('Invalid Type. Required type=Union[Type, Dict[int, Type]]')

        return route_responses
