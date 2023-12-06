import typing as t

from ellar.common.serializer import serialize_object
from ellar.pydantic import BaseModel, create_model

RequestErrorModel: t.Type[BaseModel] = create_model("Request")
WebSocketErrorModel: t.Type[BaseModel] = create_model("WebSocket")


class ValidationException(Exception):
    def __init__(self, errors: t.Sequence[t.Any]) -> None:
        self._errors = errors

    def errors(self) -> t.Sequence[t.Any]:
        return serialize_object(self._errors)  # type:ignore[no-any-return]


class RequestValidationError(ValidationException):
    def __init__(self, errors: t.Sequence[t.Any], *, body: t.Any = None) -> None:
        super().__init__(errors)
        self.body = body


class WebSocketRequestValidationError(ValidationException):
    pass
