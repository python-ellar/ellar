import typing as t

from ellar.common.decorators import set_metadata as set_meta
from ellar.openapi.constants import OPENAPI_TAG


def ApiTags(
    name: str,
    description: str = None,
    external_doc_description: str = None,
    external_doc_url: str = None,
) -> t.Callable:
    """
    =========CONTROLLER AND ROUTER DECORATORS ==============
    """
    external_doc = None
    if external_doc_url:
        external_doc = dict(
            url=external_doc_url,
            description=external_doc_description,
        )

    tag_info = dict(
        name=name,
        description=description,
        externalDocs=external_doc,
    )
    return set_meta(OPENAPI_TAG, tag_info)
