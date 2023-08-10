from ellar.common import set_metadata
from ellar.reflect import reflect


def sample_target():
    pass


def test_set_metadata_case_1():
    meta = set_metadata("abc")
    meta = meta("meta_value")
    meta(sample_target)

    assert reflect.get_metadata("abc", sample_target) == "meta_value"


def test_set_metadata_case_2():
    meta = set_metadata("abc_2", "meta_value")
    meta(sample_target)

    assert reflect.get_metadata("abc_2", sample_target) == "meta_value"
