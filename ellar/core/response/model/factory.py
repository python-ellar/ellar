import typing as t

from starlette.responses import Response

if t.TYPE_CHECKING:
    from .base import ResponseModel, ResponseModelField

T = t.TypeVar("T")


def create_response_model(
    response_model: t.Union[t.Type["ResponseModel"], t.Type[T]],
    *,
    response_type: t.Type[Response] = None,
    description: str = "Successful Response",
    schema: t.Union[t.Type["ResponseModelField"], t.Any] = None,
    **kwargs: t.Any,
) -> t.Union["ResponseModel", T]:
    _init_kwargs: t.Dict[str, t.Any] = dict(
        response_type=response_type, description=description, schema=schema
    )
    _init_kwargs.update(kwargs)
    return response_model(**_init_kwargs)
