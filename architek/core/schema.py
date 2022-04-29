import typing as t

from pydantic import BaseModel, Field, root_validator, validator

from architek.constants import ROUTE_METHODS
from architek.core.response.model import EmptyAPIResponseModel, ResponseModel

if t.TYPE_CHECKING:
    from architek.core.routing.websocket import WebSocketExtraHandler


class TResponseModel:
    @classmethod
    def __get_validators__(
        cls: t.Type["TResponseModel"],
    ) -> t.Iterable[t.Callable[..., t.Any]]:
        yield cls.validate

    @classmethod
    def validate(cls: t.Type["ResponseModel"], v: t.Any) -> t.Any:
        if not isinstance(v, ResponseModel):
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
        t.Union[t.Dict[int, t.Union[t.Type, t.Any, TResponseModel]], TResponseModel]
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
                "Expected ResponseModel | Dict[int, Any | BaseModel | ResponseModel]"
            )

        response = values["response"]
        if not response:
            values["response"] = {200: EmptyAPIResponseModel()}
        elif not isinstance(response, dict):
            values["response"] = {200: response}
        return values


class WsRouteParameters(BaseModel):
    path: str
    name: t.Optional[str] = None
    endpoint: t.Callable
    encoding: str = Field("json")
    use_extra_handler: bool = Field(False)
    extra_handler_type: t.Optional[t.Type["WebSocketExtraHandler"]] = None

    @validator("endpoint")
    def validate_endpoint(cls, value: t.Any):
        if not callable(value):
            raise ValueError("An endpoint must be a callable")
        return value

    @validator("encoding")
    def validate_encoding(cls, value: t.Any):
        if value not in ["json", "text", "bytes"]:
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


class PydanticSchema(BaseModel):
    pass
