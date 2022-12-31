import typing as t
from enum import Enum

from ellar.core.context import IExecutionContext
from ellar.serializer import Serializer, SerializerFilter, serialize_object

from ..response_types import FileResponse, Response, StreamingResponse
from .base import ResponseModel, ResponseModelField


class StreamingResponseModelInvalidContent(RuntimeError):
    pass


class ContentDispositionType(str, Enum):
    inline = "inline"
    attachment = "attachment"


class FileResponseModelSchema(Serializer):
    path: str
    media_type: t.Optional[str] = None
    filename: t.Optional[str] = None
    method: t.Optional[str] = None
    content_disposition_type: ContentDispositionType = ContentDispositionType.attachment


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
        response_args, headers = self.get_context_response(
            context=context, status_code=status_code
        )

        init_kwargs = serialize_object(self.serialize(response_obj))
        response_args.update(init_kwargs)

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
        return _response_model_field.serialize(
            response_obj, serializer_filter=serializer_filter
        )


class StreamingResponseModel(ResponseModel):
    response_type = StreamingResponse

    def get_model_field(self) -> t.Optional[t.Union[ResponseModelField, t.Any]]:
        # We don't want any schema for this.
        return None

    def create_response(
        self, context: IExecutionContext, response_obj: t.Any, status_code: int
    ) -> Response:
        response_args, headers = self.get_context_response(
            context=context, status_code=status_code
        )
        if not isinstance(response_obj, (t.AsyncGenerator, t.Generator)):
            raise StreamingResponseModelInvalidContent(
                "Content must typing.AsyncIterable OR typing.Iterable"
            )

        response = self._response_type(
            **response_args, headers=headers, content=response_obj
        )
        return response
