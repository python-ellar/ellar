from __future__ import annotations

import typing as t

from ellar.common.constants import ROUTE_METHODS
from ellar.common.interfaces import IResponseModel
from ellar.common.responses.models import EmptyAPIResponseModel, create_response_model
from ellar.common.serializer import BaseSerializer, Serializer
from ellar.pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    as_pydantic_validator,
    field_validator,
    model_validator,
)


@as_pydantic_validator("__validate_input__")
class TResponseModel:
    @classmethod
    def __validate_input__(cls, __input_value: t.Any, _: t.Any) -> t.Any:
        if not isinstance(__input_value, IResponseModel):
            raise ValueError(f"Expected ResponseModel, received: {type(__input_value)}")
        return __input_value


class RouteParameters(Serializer):
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
    ] = None

    @field_validator("methods")
    def validate_methods(cls, value: t.Any) -> t.List[str]:
        methods = [m.upper() for m in value]
        not_valid_methods = list(set(methods) - set(ROUTE_METHODS))

        if not_valid_methods:
            raise ValueError(f"Method {','.join(not_valid_methods)} not allowed")
        return methods

    @field_validator("endpoint")
    def validate_endpoint(cls, value: t.Any) -> t.Any:
        if not callable(value):  # pragma: no cover
            raise ValueError("An endpoint must be a callable")
        return value

    @model_validator(mode="before")
    def validate_root(cls, values: t.Any) -> t.Any:
        response = values.get("response")
        if not response:
            values["response"] = {200: create_response_model(EmptyAPIResponseModel)}
        elif not isinstance(response, dict):
            values["response"] = {200: response}
        return values


class WsRouteParameters(Serializer):
    path: str
    name: t.Optional[str] = None
    endpoint: t.Callable
    encoding: t.Optional[str] = Field("json")
    use_extra_handler: bool = Field(False)
    extra_handler_type: t.Optional[t.Type[t.Any]] = None
    _kwargs: t.Dict = PrivateAttr()

    def __init__(self, **data: t.Any) -> None:
        super().__init__(**data)
        self._kwargs = {}

    @field_validator("endpoint")
    def validate_endpoint(cls, value: t.Any) -> t.Any:
        return value

    @field_validator("encoding")
    def validate_encoding(cls, value: t.Any) -> t.Any:
        if value not in ["json", "text", "bytes", None]:
            raise ValueError(
                f"Encoding type not supported. Once [json | text | bytes]. Received: {value}"
            )
        return value

    @field_validator("extra_handler_type")
    def validate_extra_handler_type(cls, value: t.Any) -> t.Any:
        from ellar.core.routing.websocket import WebSocketExtraHandler

        if value and not issubclass(value, WebSocketExtraHandler):
            raise ValueError(
                f"Expected value to be type of {WebSocketExtraHandler}. but got {value}"
            )
        return value

    def dict(self, *args: t.Any, **kwargs: t.Any) -> t.Dict:
        data = super().dict(*args, **kwargs)
        data.update(self._kwargs)
        return data

    def add_websocket_handler(self, handler_name: str, handler: t.Callable) -> None:
        self._kwargs[handler_name] = handler
