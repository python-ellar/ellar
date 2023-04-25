from ellar.reflect import reflect
from ellar.socket_io import on_connected, on_disconnected
from ellar.socket_io.constants import (
    CONNECTION_EVENT,
    DISCONNECT_EVENT,
    MESSAGE_MAPPING_METADATA,
)


def test_on_connected_decorator_works():
    @on_connected()
    def sample_function():
        pass

    assert getattr(sample_function, MESSAGE_MAPPING_METADATA)
    assert reflect.get_metadata_or_raise_exception(CONNECTION_EVENT, sample_function)


def test_on_disconnected_decorator_works():
    @on_disconnected()
    def sample_function():
        pass

    assert getattr(sample_function, MESSAGE_MAPPING_METADATA)
    assert reflect.get_metadata_or_raise_exception(DISCONNECT_EVENT, sample_function)
