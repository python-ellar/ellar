import typing as t

from ellar.common.compatible import AttributeDict
from ellar.common.decorators import set_metadata as set_meta
from ellar.common.exceptions import ImproperConfiguration
from ellar.openapi.constants import OPENAPI_OPERATION_KEY


def api_info(
    operation_id: t.Optional[str] = None,
    summary: t.Optional[str] = None,
    description: t.Optional[str] = None,
    tags: t.Optional[t.List[str]] = None,
    deprecated: t.Optional[bool] = None,
    **kwargs: t.Any,
) -> t.Callable:
    """
    ========= ROUTE FUNCTION DECORATOR ==============

    Route Function OpenAPI extra information
    :param operation_id: OpenAPI operational id
    :param summary: summary
    :param description: description
    :param tags: tags
    :param deprecated:
    :return:
    """
    if tags and not isinstance(tags, list):
        raise ImproperConfiguration("tags must be a sequence of str eg, [tagA, tagB]")

    return set_meta(
        OPENAPI_OPERATION_KEY,
        AttributeDict(
            operation_id=operation_id,
            summary=summary,
            description=description,
            deprecated=deprecated,
            tags=tags,
            **kwargs,
        ),
    )
