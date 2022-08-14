import typing as t

from ellar.compatible import AttributeDict
from ellar.constants import OPENAPI_KEY

from .base import set_meta


def openapi_info(
    operation_id: t.Optional[str] = None,
    summary: t.Optional[str] = None,
    description: t.Optional[str] = None,
    tags: t.Optional[t.List[str]] = None,
    deprecated: t.Optional[bool] = None,
) -> t.Callable:
    return set_meta(
        OPENAPI_KEY,
        AttributeDict(
            operation_id=operation_id,
            summary=summary,
            description=description,
            deprecated=deprecated,
            tags=tags,
        ),
        default_value=AttributeDict(),
    )
