import typing as t

from .base import set_meta


def openapi(
    operation_id: t.Optional[str] = None,
    summary: t.Optional[str] = None,
    description: t.Optional[str] = None,
    tags: t.Optional[t.List[str]] = None,
    deprecated: t.Optional[bool] = None,
) -> t.Callable:
    return set_meta(
        "openapi",
        dict(
            operation_id=operation_id,
            summary=summary,
            description=description,
            deprecated=deprecated,
            tags=tags,
        ),
    )
