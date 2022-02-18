import typing as t

from pydantic import BaseModel, validator, Field

from starletteapi.constants import ROUTE_METHODS
from starletteapi.responses.model import EmptyAPIResponseModel


class RouteParameters(BaseModel):
    path: str
    methods: t.List[str]
    endpoint: t.Callable
    operation_id: t.Optional[str] = None
    summary: t.Optional[str] = None
    description: t.Optional[str] = None
    tags: t.Optional[t.List[str]] = None
    deprecated: t.Optional[bool] = None
    name: t.Optional[str] = None
    include_in_schema: bool = True
    response: t.Union[t.Dict[int, t.Union[t.Type, t.Any]], t.Type, None] = None

    @validator('methods')
    def validate_methods(cls, value):
        methods = list(map(lambda m: m.upper(), value))
        not_valid_methods = list(set(methods) - set(ROUTE_METHODS))

        if not_valid_methods:
            raise ValueError(
                f"Method {','.join(not_valid_methods)} not allowed"
            )
        return methods

    @validator('endpoint')
    def validate_endpoint(cls, value):
        assert callable(value), "An endpoint must be a callable"
        return value

    @validator('response')
    def validate_response(cls, value):
        if not value:
            return {200: EmptyAPIResponseModel()}
        return value


class WsRouteParameters(BaseModel):
    path: str
    name: t.Optional[str] = None
    endpoint: t.Callable

    @validator('endpoint')
    def validate_endpoint(cls, value):
        assert callable(value), "An endpoint must be a callable"
        return value


class ValidationError(BaseModel):
    loc: t.List[str] = Field(..., title='Location')
    msg: str = Field(..., title='Message')
    type: str = Field(..., title='Error Type')


class HTTPValidationError(BaseModel):
    detail: t.List[ValidationError] = Field(..., title='Details')


class PydanticSchema(BaseModel):
    pass
