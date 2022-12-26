import typing as t

from pydantic import BaseModel, ValidationError, create_model
from pydantic.error_wrappers import ErrorList

RequestErrorModel: t.Type[BaseModel] = create_model("Request")
WebSocketErrorModel: t.Type[BaseModel] = create_model("WebSocket")


class RequestValidationError(ValidationError):
    def __init__(self, errors: t.Sequence[ErrorList]) -> None:
        super().__init__(errors, RequestErrorModel)


class WebSocketRequestValidationError(ValidationError):
    def __init__(self, errors: t.Sequence[ErrorList]) -> None:
        super().__init__(errors, WebSocketErrorModel)
