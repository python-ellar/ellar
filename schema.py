from typing import Optional, List, Union, Type, Dict, Tuple, Callable, Any

from pydantic import BaseModel, validator

from starletteapi.constants import ROUTE_METHODS
from starletteapi.responses.model import EmptyAPIResponseModel


class RouteParameters(BaseModel):
    path: str
    methods: List[str]
    endpoint: Callable
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    deprecated: Optional[bool] = None
    name: Optional[str] = None
    include_in_schema: bool = True
    response: Union[Dict[int, Union[Type, Any]], Type, None] = None

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
    name: Optional[str] = None
    endpoint: Callable

    @validator('endpoint')
    def validate_endpoint(cls, value):
        assert callable(value), "An endpoint must be a callable"
        return value


class PydanticSchema(BaseModel):
    pass

