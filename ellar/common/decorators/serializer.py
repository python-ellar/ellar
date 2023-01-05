import typing as t

from ellar.constants import SERIALIZER_FILTER_KEY

from .base import set_metadata as set_meta


def serializer_filter(
    include: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None,
    exclude: t.Optional[
        t.Union[t.Set[t.Union[int, str]], t.Mapping[t.Union[int, str], t.Any]]
    ] = None,
    by_alias: bool = True,
    skip_defaults: t.Optional[bool] = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
) -> t.Callable:
    """
    ========= ROUTE FUNCTION DECORATOR ==============

    defines route function pydantic filters for data serialization
    :param include:
    :param exclude:
    :param by_alias:
    :param skip_defaults:
    :param exclude_unset:
    :param exclude_defaults:
    :param exclude_none:
    :return:
    """
    from ellar.serializer import SerializerFilter

    return set_meta(
        SERIALIZER_FILTER_KEY,
        SerializerFilter(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        ),
    )
