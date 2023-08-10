import typing as t

from starlette.responses import Response

from .base import ResponseModel, ResponseModelField

T = t.TypeVar("T")


def create_response_model(
    response_model: t.Union[t.Type["ResponseModel"], t.Type[T]],
    *,
    response_type: t.Optional[t.Type[Response]] = None,
    description: t.Optional[str] = None,
    model_field_or_schema: t.Union[t.Type["ResponseModelField"], t.Any, None] = None,
    **kwargs: t.Any,
) -> t.Union["ResponseModel", T]:
    _init_kwargs: t.Dict[str, t.Any] = {
        "response_type": response_type,
        "description": description,
        "model_field_or_schema": model_field_or_schema,
    }
    _init_kwargs.update(kwargs)
    return response_model(**_init_kwargs)
