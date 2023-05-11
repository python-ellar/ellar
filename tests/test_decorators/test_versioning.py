from ellar.common import Version
from ellar.common.constants import VERSIONING_KEY
from ellar.reflect import reflect


@Version(1, 2, 3)
def endpoint_versioning_func():
    pass  # pragma: no cover


def test_version_decorator_define_endpoint_version_meta():
    assert reflect.has_metadata(VERSIONING_KEY, endpoint_versioning_func)
    versions = reflect.get_metadata(VERSIONING_KEY, endpoint_versioning_func)
    for item in [1, 2, 3]:
        assert str(item) in versions
