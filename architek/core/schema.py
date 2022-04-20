import typing as t

from pydantic import BaseModel, Field, validator

from architek.constants import ROUTE_METHODS
from architek.core.response.model import EmptyAPIResponseModel, ResponseModel

if t.TYPE_CHECKING:
    from architek.core.routing.websocket import WebSocketExtraHandler


class RouteParameters(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    path: str
    methods: t.List[str]
    endpoint: t.Callable
    name: t.Optional[str] = None
    include_in_schema: bool = True
    response: t.Union[t.Dict[int, t.Union[t.Type, t.Any]], ResponseModel, None] = None

    @validator("methods")
    def validate_methods(cls, value: t.Any):
        methods = list(map(lambda m: m.upper(), value))
        not_valid_methods = list(set(methods) - set(ROUTE_METHODS))

        if not_valid_methods:
            raise ValueError(f"Method {','.join(not_valid_methods)} not allowed")
        return methods

    @validator("endpoint")
    def validate_endpoint(cls, value: t.Any):
        assert callable(value), "An endpoint must be a callable"
        return value

    @validator("response")
    def validate_response(cls, value: t.Any):
        if not value:
            return {200: EmptyAPIResponseModel()}
        if not isinstance(value, dict):
            return {200: value}
        return value


class WsRouteParameters(BaseModel):
    path: str
    name: t.Optional[str] = None
    endpoint: t.Callable
    encoding: str = Field("json")
    use_extra_handler: bool = Field(False)
    extra_handler_type: t.Optional[t.Type["WebSocketExtraHandler"]] = None

    @validator("endpoint")
    def validate_endpoint(cls, value: t.Any):
        assert callable(value), "An endpoint must be a callable"
        return value

    @validator("encoding")
    def validate_encoding(cls, value: t.Any):
        assert value in ["json", "text", "bytes"], "An endpoint must be a callable"
        return value


class ValidationError(BaseModel):
    loc: t.List[str] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class HTTPValidationError(BaseModel):
    detail: t.List[ValidationError] = Field(..., title="Details")


class PydanticSchema(BaseModel):
    pass
