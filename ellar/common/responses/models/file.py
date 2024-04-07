import typing as t
from enum import Enum

from ellar.common.interfaces import IExecutionContext
from ellar.common.logging import request_logger
from ellar.common.serializer import Serializer, SerializerFilter
from ellar.pydantic import field_validator

from ..response_types import FileResponse, Response, StreamingResponse
from .base import ResponseModel, ResponseModelField


class ContentDispositionType(str, Enum):
    inline = "inline"
    attachment = "attachment"


class FileResponseModelSchema(Serializer):
    path: str
    media_type: t.Optional[str] = None
    filename: t.Optional[str] = None
    method: t.Optional[str] = None
    content_disposition_type: ContentDispositionType = ContentDispositionType.attachment


class StreamResponseModelSchema(Serializer):
    media_type: t.Optional[str] = None
    content: t.Any

    @field_validator("content", mode="before")
    def pre_validate_content(cls, value: t.Dict) -> t.Any:
        if not isinstance(value, (t.AsyncGenerator, t.Generator)):
            raise ValueError("Content must typing.AsyncIterable OR typing.Iterable")
        return value


class FileResponseModel(ResponseModel):
    __slots__ = ("_file_init_schema",)

    response_type: t.Type[Response] = FileResponse
    file_init_schema_type = FileResponseModelSchema

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super(FileResponseModel, self).__init__(*args, **kwargs)
        self._file_init_schema = self._get_model_field_from_schema(
            self.file_init_schema_type
        )

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        request_logger.debug(
            f"Creating Response from returned Handler value - '{self.__class__.__name__}'"
        )
        response_args, headers = self.get_context_response(
            context=context, status_code=status_code
        )

        init_kwargs = self.serialize(response_obj)
        response_args.update(init_kwargs)  # type:ignore[arg-type]

        response = self._response_type(
            **response_args,
            headers=headers,
        )
        return response

    def get_init_kwargs_schema(self) -> ResponseModelField:
        assert self._file_init_schema
        return self._file_init_schema

    def get_model_field(self) -> t.Optional[t.Union[ResponseModelField, t.Any]]:
        # We don't want any schema for this.
        return None

    def serialize(
        self,
        response_obj: t.Any,
        serializer_filter: t.Optional[SerializerFilter] = None,
    ) -> t.Union[t.List[t.Dict], t.Dict, t.Any]:
        _response_model_field = self.get_init_kwargs_schema()
        assert _response_model_field, "ResponseModelField is required"
        return _response_model_field.prep_and_serialize(
            response_obj, serializer_filter=serializer_filter
        )


class StreamingResponseModel(ResponseModel):
    response_type = StreamingResponse
    file_schema_type = StreamResponseModelSchema

    def get_model_field(self) -> t.Optional[t.Union[ResponseModelField, t.Any]]:
        # We don't want any schema for this.
        return None

    def serialize(
        self,
        response_obj: t.Any,
        serializer_filter: t.Optional[SerializerFilter] = None,
    ) -> t.Union[t.List[t.Dict], t.Dict, t.Any, StreamResponseModelSchema]:
        if isinstance(response_obj, (t.AsyncGenerator, t.Generator)):
            response_obj = {"content": response_obj, "media_type": self.media_type}

        value = self.file_schema_type.from_orm(response_obj)
        return value

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        request_logger.debug(
            f"Creating Response from returned Handler value - '{self.__class__.__name__}'"
        )

        response_args, headers = self.get_context_response(
            context=context, status_code=status_code
        )
        data = t.cast(StreamResponseModelSchema, self.serialize(response_obj))

        response = self._response_type(
            **response_args,
            headers=headers,
            content=data.content,
            media_type=data.media_type or self.media_type,
        )
        return response
