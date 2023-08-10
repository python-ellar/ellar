from ellar.core.services import Reflector
from ellar.reflect import reflect

reflector = Reflector()


class SampleTarget:
    pass


def test_should_reflect_metadata():
    key = "key"
    value = "value"
    reflect.define_metadata(key, value, SampleTarget)
    assert reflector.get(key, SampleTarget) == value


def test_should_reflect_metadata_of_all_targets():
    key = "key"
    value = "value"
    reflect.define_metadata(key, value, SampleTarget)
    assert reflector.get_all(key, *[SampleTarget]) == [value]


def test_should_return_an_empty_array_when_there_are_no_targets():
    key = "key"
    assert reflector.get_all_and_merge(key, *[]) == []


def test_should_reflect_metadata_of_all_targets_and_concat_arrays():
    key = "key"
    value = "value"
    reflect.define_metadata(key, [value], SampleTarget)
    assert reflector.get_all_and_merge(key, *[SampleTarget, SampleTarget]) == [
        value,
        value,
    ]

    reflect.define_metadata("key1", value, SampleTarget)
    assert reflector.get_all_and_merge("key1", *[SampleTarget]) == [value]


def test_should_reflect_metadata_of_all_targets_in_an_arrays():
    key = "key"
    value = "value"
    reflect.define_metadata(key, value, SampleTarget)
    assert reflector.get_all_and_merge(
        key, *[SampleTarget, SampleTarget, SampleTarget]
    ) == [value, value, value]


def test_should_reflect_metadata_of_all_targets_and_merge_an_object(random_type):
    key = "key"
    value = {"test": "test"}
    reflect.define_metadata(key, value, SampleTarget)
    assert reflector.get_all_and_merge(key, *[SampleTarget, SampleTarget]) == value


def test_should_reflect_metadata_of_all_targets_and_merge_different_objects(
    random_type,
):
    key = "key"
    value = {"test": "test"}
    reflect.define_metadata(key, value, SampleTarget)
    reflect.define_metadata(key, {"test_2": "test_2"}, SampleTarget)
    assert reflector.get_all_and_merge(key, *[SampleTarget, SampleTarget]) == {
        "test": "test",
        "test_2": "test_2",
    }


def test_should_reflect_metadata_of_all_targets_and_return_a_first_not_undefined_value():
    key = "key"
    value = "value"
    reflect.define_metadata(key, value, SampleTarget)
    assert reflector.get_all_and_override(key, *[SampleTarget, SampleTarget]) == value
