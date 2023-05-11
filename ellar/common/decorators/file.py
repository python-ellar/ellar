import inspect
import typing as t
import warnings

from ellar.common.constants import NOT_SET, RESPONSE_OVERRIDE_KEY
from ellar.common.interfaces import IResponseModel
from ellar.common.shortcuts import fail_silently

from ..responses.models import FileResponseModel, StreamingResponseModel
from .base import set_metadata as set_meta


def file(media_type: t.Optional[str] = NOT_SET, streaming: bool = False) -> t.Callable:
    """
    ========= ROUTE FUNCTION DECORATOR ==============

    Renders route function response as FileResponse


    :param media_type: MIME Type.
    :param streaming: Defaults ResponseModel to use. False=FileResponseModel, True=StreamingResponseModel.
    IF STREAMING == FALSE:
        Decorated Function is expected to return an object of dict with values keys:
            {
                path: mandatory path to file,
                media_type: optional
                filename: optional filename
                method: optional HTTP Method
                content_disposition_type: `attachment` | `inline`
                status_code: 200
            }
    IF STREAMING == TRUE
        Decorated Function is expected to return:
            typing.Iterator[Content] OR typing.AsyncIterable[Content]
    :return: typing.Callable
    """
    if media_type is not NOT_SET:
        assert isinstance(media_type, str), "File decorator must invoked eg. @file()"

    if media_type is NOT_SET:
        media_type = "text/plain"

    def _decorator(func: t.Union[t.Callable, t.Any]) -> t.Union[t.Callable, t.Any]:
        if not inspect.isfunction(func):
            line_nos = fail_silently(
                inspect.getsourcelines, getattr(func, "endpoint", func)
            )
            warnings.warn_explicit(
                UserWarning(
                    "\n@file should be used only as a function decorator. "
                    "\nUse @file before @HTTPMethod decorator."
                ),
                category=None,
                filename=inspect.getfile(getattr(func, "endpoint", func)),
                lineno=line_nos[1] if line_nos and len(line_nos) > 0 else None,
                source=None,
            )
            return func

        response: IResponseModel
        if streaming:
            response = StreamingResponseModel(media_type=media_type)
        else:
            response = FileResponseModel(media_type=media_type)

        target_decorator = set_meta(RESPONSE_OVERRIDE_KEY, {200: response})
        return target_decorator(func)

    return _decorator
