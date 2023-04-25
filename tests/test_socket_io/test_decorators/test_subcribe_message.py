from ellar.reflect import reflect
from ellar.socket_io import subscribe_message
from ellar.socket_io.constants import MESSAGE_MAPPING_METADATA, MESSAGE_METADATA


def test_subscribe_message_works():
    @subscribe_message("sample")
    def sample_function():
        pass

    assert getattr(sample_function, MESSAGE_MAPPING_METADATA)
    assert (
        reflect.get_metadata_or_raise_exception(MESSAGE_METADATA, sample_function)
        == "sample"
    )

    @subscribe_message
    def sample_function2():
        pass

    assert getattr(sample_function2, MESSAGE_MAPPING_METADATA)
    assert (
        reflect.get_metadata_or_raise_exception(MESSAGE_METADATA, sample_function2)
        == "sample_function2"
    )
