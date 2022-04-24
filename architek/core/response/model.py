import typing as t
from dataclasses import is_dataclass

from pydantic import BaseModel
from pydantic.fields import ModelField

from architek.core.context import IExecutionContext
from architek.core.converters import TypeDefinitionConverter
from architek.core.exceptions import RequestValidationError
from architek.core.helper.modelfield import create_model_field
from architek.serializer import (
    BaseSerializer,
    DataClassSerializer,
    PydanticSerializer,
    PydanticSerializerBase,
    convert_dataclass_to_pydantic_model,
    serialize_object,
)

from .responses import JSONResponse, Response


class ResponseResolver(t.NamedTuple):
    status_code: int
    response_model: "ResponseModel"
    response_object: t.Any


class ResponseModel:
    def __init__(
        self,
        response_type: t.Type[Response],
        description: str = "Successful Response",
        **kwargs: t.Any,
    ) -> None:
        self.response_type = response_type
        self.media_type = getattr(
            response_type or {}, "media_type", kwargs.get("media_type")
        )
        self.description = description
        self.meta = kwargs

    def serialize(self, response_obj: t.Any) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        return response_obj

    def get_model_field(self) -> t.Optional[ModelField]:
        return None

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        """Cant create custom responses, Please override this function to create a custom response"""
        response_args, headers = self.get_context_response(context=context)
        response = self.response_type(
            **response_args, content=response_obj, headers=headers
        )
        return response

    @classmethod
    def get_context_response(
        cls, context: IExecutionContext, **kwargs: t.Any
    ) -> t.Tuple[t.Dict, t.Dict]:
        response_args = dict(kwargs)
        if context.has_response:
            endpoint_response = context.get_response()
            response_args = dict(background=endpoint_response.background)
            if endpoint_response.status_code > 0:
                response_args["status_code"] = endpoint_response.status_code
            return response_args, dict(endpoint_response.headers)
        return response_args, {}

    def __deepcopy__(self, memodict: t.Dict = {}) -> "ResponseModel":
        return self.__copy__(memodict)

    def __copy__(self, memodict: t.Dict = {}) -> "ResponseModel":
        return self


class _JSONResponseModel(ResponseModel):
    def __init__(self, **kwargs: t.Any) -> None:
        kwargs.update(response_type=JSONResponse)
        super().__init__(**kwargs)
        model_field = create_model_field(
            name="response_model", type_=dict, model_field_class=ResponseModelField
        )
        self.response_model_field = model_field

    def get_model_field(self) -> t.Optional[ModelField]:
        return self.response_model_field

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        json_response_class = t.cast(
            t.Type[JSONResponse], context.get_app().config.DEFAULT_JSON_CLASS
        )
        response_args, headers = self.get_context_response(context=context)
        response = json_response_class(
            **response_args, content=self.serialize(response_obj), headers=headers
        )
        return response


class APIResponseModel(_JSONResponseModel):
    def __init__(
        self,
        response_schema: t.Type[BaseModel],
        description: str = "Successful Response",
    ) -> None:
        super().__init__(description=description)

        new_response_schema = ResponseTypeDefinitionConverter(
            response_schema
        ).re_group_outer_type()
        model_field = create_model_field(
            name="response_model",
            type_=new_response_schema,
            model_field_class=ResponseModelField,
        )
        self.response_model_field: "ResponseModelField" = t.cast(
            ResponseModelField, model_field
        )

    def serialize(self, response_obj: t.Any) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        return self.response_model_field.serialize(response_obj)


class EmptyAPIResponseModel(_JSONResponseModel):
    def serialize(self, response_obj: t.Any) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        try:
            # try an serialize object
            return serialize_object(response_obj)
        except Exception:
            """Failed to auto serialize object"""
        return response_obj


class ResponseModelField(ModelField):
    def validate_object(self, obj: t.Any) -> t.Any:
        values, error = self.validate(obj, {}, loc=(self.alias,))
        if error:
            _errors = list(error) if isinstance(error, list) else error
            raise RequestValidationError(errors=_errors)  # type: ignore
        return values

    def serialize(self, obj: t.Any) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        values = self.validate_object(obj=obj)
        return serialize_object(values)


class RouteResponseExecution(Exception):
    pass


class ResponseTypeDefinitionConverter(TypeDefinitionConverter):
    _registry: t.Dict[t.Any, t.Type[BaseSerializer]] = {}

    def _get_modified_type(self, outer_type_: t.Type) -> t.Type[BaseSerializer]:
        if not isinstance(outer_type_, type):
            raise Exception(f"{outer_type_} is not a type")

        if issubclass(outer_type_, DataClassSerializer):
            schema_model = outer_type_.get_pydantic_model()
            cls = type(outer_type_.__name__, (schema_model, PydanticSerializerBase), {})
            return t.cast(t.Type[BaseSerializer], cls)

        if isinstance(outer_type_, type) and issubclass(outer_type_, (BaseSerializer,)):
            return outer_type_

        if issubclass(outer_type_, BaseModel):
            if not outer_type_.Config.orm_mode:
                outer_type_.Config.orm_mode = True
            cls = type(outer_type_.__name__, (outer_type_, PydanticSerializer), dict())
            return t.cast(t.Type[BaseSerializer], cls)

        if is_dataclass(outer_type_):
            if hasattr(outer_type_, "__pydantic_model__"):
                schema_model = outer_type_.__pydantic_model__
                return self._get_modified_type(t.cast(type, schema_model))
            return self._get_modified_type(
                t.cast(type, convert_dataclass_to_pydantic_model(outer_type_))
            )

        cls = type(outer_type_.__name__, (outer_type_, PydanticSerializer), dict())

        return t.cast(t.Type[BaseSerializer], cls)

    def get_modified_type(self, outer_type_: t.Type) -> t.Type[BaseSerializer]:
        if outer_type_ not in self._registry:
            self._registry[outer_type_] = self._get_modified_type(outer_type_)
        return self._registry[outer_type_]


class RouteResponseModel:
    __slots__ = ("models",)

    def __init__(self, route_responses: t.Union[t.Type, t.Dict[int, t.Type]]) -> None:
        self.models: t.Dict[int, ResponseModel] = {}
        self.convert_route_responses_to_response_models(route_responses)

    def convert_route_responses_to_response_models(
        self, route_responses: t.Union[t.Type, t.Dict[int, t.Type]]
    ) -> None:
        _route_responses = self.get_route_responses_as_dict(route_responses)
        for status_code, response_schema in _route_responses.items():
            assert (
                isinstance(status_code, int) or status_code == Ellipsis
            ), "status_code must be a number"
            description: str = "Successful Response"
            if isinstance(response_schema, (tuple, list)):
                response_schema, description = response_schema

            if isinstance(response_schema, type) and issubclass(
                response_schema, Response
            ):
                self.models[status_code] = ResponseModel(
                    response_schema, description=description
                )
                continue

            if isinstance(response_schema, ResponseModel):
                self.models[status_code] = response_schema
                continue

            self.models[status_code] = APIResponseModel(
                t.cast(t.Type[BaseModel], response_schema), description=description
            )

    def response_resolver(
        self,
        ctx: IExecutionContext,
        endpoint_response_content: t.Union[t.Any, t.Tuple[int, t.Any]],
    ) -> ResponseResolver:
        status_code: int = 200
        response_obj: t.Any = endpoint_response_content
        response_model: t.Optional[ResponseModel] = None

        if len(self.models) == 1:
            status_code = list(self.models.keys())[0]

        if ctx.has_response and ctx.get_response().status_code > 0:
            status_code = ctx.get_response().status_code

        if isinstance(response_obj, tuple) and len(response_obj) == 2:
            status_code, response_obj = endpoint_response_content

        if status_code in self.models:
            response_model = self.models[status_code]
        elif Ellipsis in self.models:
            response_model = self.models[Ellipsis]  # type: ignore
        else:
            RouteResponseExecution(
                f"No response Schema with status_code={status_code} in response {self.models.keys()}"
            )
        response_model = t.cast(ResponseModel, response_model)
        return ResponseResolver(status_code, response_model, response_obj)

    def process_response(
        self, ctx: IExecutionContext, response_obj: t.Union[t.Any, t.Tuple[int, t.Any]]
    ) -> Response:
        if isinstance(response_obj, Response):
            return response_obj

        resolver = self.response_resolver(ctx, response_obj)
        return resolver.response_model.create_response(
            status_code=resolver.status_code,
            context=ctx,
            response_obj=resolver.response_object,
        )

    @classmethod
    def get_route_responses_as_dict(
        cls, route_responses: t.Union[t.Type, t.Dict[int, t.Type]]
    ) -> t.Dict[int, t.Type]:
        _route_responses: t.Dict[int, t.Type] = {}

        if not isinstance(route_responses, (t.Sequence, dict)):
            if isinstance(route_responses, type) and issubclass(
                route_responses, Response
            ):
                if (
                    route_responses.media_type
                    and route_responses.media_type.lower() == "application/json"
                ):
                    raise RouteResponseExecution("JSONResponse type is not required.")
            _route_responses[200] = route_responses
            return _route_responses

        if not isinstance(route_responses, dict):
            raise RouteResponseExecution(
                "Invalid Type. Required type=Union[Type, Dict[int, Type]]"
            )

        return route_responses
