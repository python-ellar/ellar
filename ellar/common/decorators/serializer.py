import typing as t

from ellar.common.constants import SERIALIZER_FILTER_KEY
from ellar.common.serializer import SerializerFilter

from .base import set_metadata as set_meta


def serializer_filter(
    include: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None,
    exclude: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> t.Callable:
    """
    ========= ROUTE FUNCTION DECORATOR ==============

    defines route function pydantic filters for data serialization

    :param include: Fields to include
    :param exclude: Fields to exclude
    :param by_alias: Whether to use alias
    :param exclude_unset: Whether to exclude unset fields
    :param exclude_defaults: Whether to exclude default fields
    :param exclude_none: Whether to exclude none fields

    ### Example

    ```python
    @get("/")
    @serializer_filter(include={"id", "username"})
    def index():
        return {"id": 1, "username": "admin", "password": "password"}
    ```
    """

    return set_meta(
        SERIALIZER_FILTER_KEY,
        SerializerFilter(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        ),
    )
