from ellar.common import serializer_filter
from ellar.common.constants import SERIALIZER_FILTER_KEY
from ellar.common.serializer import SerializerFilter
from ellar.reflect import reflect


@serializer_filter(
    include={"test1", "test2"},
    exclude_none=True,
    by_alias=False,
    exclude={"exclude1", "exclude2"},
    skip_defaults=None,
    exclude_unset=True,
    exclude_defaults=True,
)
def serializer_filter_decorator_test():
    pass  # pragma: no cover


def test_serializer_filter_decorator_creates_serializer_filter():
    assert reflect.has_metadata(SERIALIZER_FILTER_KEY, serializer_filter_decorator_test)
    serializer_filter_data = reflect.get_metadata(
        SERIALIZER_FILTER_KEY, serializer_filter_decorator_test
    )

    assert isinstance(serializer_filter_data, SerializerFilter)
    for include_item in ["test1", "test2"]:
        assert include_item in serializer_filter_data.include

    assert serializer_filter_data.exclude_none is True
    assert serializer_filter_data.by_alias is False

    for exclude_item in ["exclude1", "exclude2"]:
        assert exclude_item in serializer_filter_data.exclude

    assert serializer_filter_data.skip_defaults is None

    assert serializer_filter_data.exclude_unset is True
    assert serializer_filter_data.exclude_defaults is True
