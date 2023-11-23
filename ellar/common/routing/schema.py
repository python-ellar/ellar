import typing as t

from ellar.common.constants import ROUTE_METHODS
from ellar.common.interfaces import IResponseModel
from ellar.common.responses.models import EmptyAPIResponseModel, create_response_model
from ellar.common.routing.websocket import WebSocketExtraHandler
from ellar.common.serializer import BaseSerializer
from pydantic import BaseModel, Field, PrivateAttr, root_validator, validator


class TResponseModel:
    @classmethod
    def __get_validators__(
        cls: t.Type["TResponseModel"],
    ) -> t.Any:
        yield cls.validate  # type:ignore[misc]

    @classmethod
    def validate(cls: t.Type["IResponseModel"], v: t.Any) -> t.Any:  # type:ignore[misc]
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
    def validate_methods(cls, value: t.Any) -> t.List[str]:
        methods = [m.upper() for m in value]
        not_valid_methods = list(set(methods) - set(ROUTE_METHODS))

        if not_valid_methods:
            raise ValueError(f"Method {','.join(not_valid_methods)} not allowed")
        return methods

    @validator("endpoint")
    def validate_endpoint(cls, value: t.Any) -> t.Any:
        if not callable(value):  # pragma: no cover
            raise ValueError("An endpoint must be a callable")
        return value

    @root_validator
    def validate_root(cls, values: t.Any) -> t.Any:
        if "response" not in values:  # pragma: no cover
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
    _kwargs: t.Dict = PrivateAttr()

    def __init__(self, **data: t.Any) -> None:
        super().__init__(**data)
        self._kwargs = {}

    @validator("endpoint")
    def validate_endpoint(cls, value: t.Any) -> t.Any:
        return value

    @validator("encoding")
    def validate_encoding(cls, value: t.Any) -> t.Any:
        if value not in ["json", "text", "bytes", None]:
            raise ValueError(
                f"Encoding type not supported. Once [json | text | bytes]. Received: {value}"
            )
        return value

    def dict(self, *args: t.Any, **kwargs: t.Any) -> t.Dict:
        data = super().dict(*args, **kwargs)
        data.update(self._kwargs)
        return data

    def add_websocket_handler(self, handler_name: str, handler: t.Callable) -> None:
        self._kwargs[handler_name] = handler
