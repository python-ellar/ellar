import typing as t

from pydantic import BaseModel, Field, root_validator, validator

from ellar.constants import ROUTE_METHODS
from ellar.core.response.model import (
    EmptyAPIResponseModel,
    IResponseModel,
    create_response_model,
)
from ellar.serializer import BaseSerializer, Serializer

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.routing.websocket import WebSocketExtraHandler


class TResponseModel:
    @classmethod
    def __get_validators__(
        cls: t.Type["TResponseModel"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["IResponseModel"], v: t.Any) -> t.Any:
        if not isinstance(v, IResponseModel):
            raise ValueError(f"Expected ResponseModel, received: {type(v)}")
        return v


class RouteParameters(BaseModel):
    class Config:
        pass
        # arbitrary_types_allowed = True

    path: str
    methods: t.List[str]
    endpoint: t.Callable
    name: t.Optional[str] = None
    include_in_schema: bool = True
    response: t.Optional[
        t.Union[
            t.Dict[int, t.Union[t.Type, t.Any, TResponseModel]],
            TResponseModel,
            t.Type[BaseModel],
            t.Type[BaseSerializer],
            t.Any,
        ]
    ]

    @validator("methods")
    def validate_methods(cls, value: t.Any):
        methods = list(map(lambda m: m.upper(), value))
        not_valid_methods = list(set(methods) - set(ROUTE_METHODS))

        if not_valid_methods:
            raise ValueError(f"Method {','.join(not_valid_methods)} not allowed")
        return methods

    @validator("endpoint")
    def validate_endpoint(cls, value: t.Any):
        if not callable(value):
            raise ValueError("An endpoint must be a callable")
        return value

    @root_validator
    def validate_root(cls, values: t.Any):
        if "response" not in values:
            raise ValueError(
                "Expected "
                "IResponseModel | Dict[int, Any | Type[BaseModel] | "
                "Type[BaseSerializer] | IResponseModel]  | Type[BaseModel] | Type[BaseSerializer]"
            )

        response = values["response"]
        if not response:
            values["response"] = {200: create_response_model(EmptyAPIResponseModel)}
        elif not isinstance(response, dict):
            values["response"] = {200: response}
        return values


class WsRouteParameters(BaseModel):
    path: str
    name: t.Optional[str] = None
    endpoint: t.Callable
    encoding: t.Optional[str] = Field("json")
    use_extra_handler: bool = Field(False)
    extra_handler_type: t.Optional[t.Type["WebSocketExtraHandler"]] = None

    @validator("endpoint")
    def validate_endpoint(cls, value: t.Any):
        return value

    @validator("encoding")
    def validate_encoding(cls, value: t.Any):
        if value not in ["json", "text", "bytes", None]:
            raise ValueError(
                f"Encoding type not supported. Once [json | text | bytes]. Received: {value}"
            )
        return value


class ValidationError(BaseModel):
    loc: t.List[str] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class HTTPValidationError(BaseModel):
    detail: t.List[ValidationError] = Field(..., title="Details")


class Schema(Serializer):
    pass
