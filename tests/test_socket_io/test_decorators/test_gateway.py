import pytest
from ellar.auth.guards import GuardHttpBearerAuth
from ellar.common import UseGuards
from ellar.common.constants import CONTROLLER_CLASS_KEY, GUARDS_KEY
from ellar.common.utils import get_name
from ellar.reflect import reflect
from ellar.socket_io import WebSocketGateway, subscribe_message
from ellar.socket_io.constants import (
    GATEWAY_MESSAGE_HANDLER_KEY,
    GATEWAY_METADATA,
    GATEWAY_OPTIONS,
    GATEWAY_WATERMARK,
    MESSAGE_METADATA,
)
from ellar.socket_io.model import GatewayBase, GatewayType


@WebSocketGateway(path="/ws", namespace="/some-namespace")
@UseGuards(GuardHttpBearerAuth)
class SampleWithoutGateway:
    pass


@WebSocketGateway(path="/ws", namespace="/some-namespace")
class SampleWithGateway(GatewayBase):
    pass


@WebSocketGateway
class SampleMarkAsGateway:
    pass


@pytest.mark.parametrize(
    "gateway, watermark, options",
    [
        (
            SampleWithoutGateway,
            True,
            {
                "async_mode": "asgi",
                "cors_allowed_origins": "*",
                "namespace": "/some-namespace",
            },
        ),
        (
            SampleWithGateway,
            False,
            {
                "async_mode": "asgi",
                "cors_allowed_origins": "*",
                "namespace": "/some-namespace",
            },
        ),
        (
            SampleMarkAsGateway,
            True,
            {"async_mode": "asgi", "cors_allowed_origins": "*"},
        ),
    ],
)
def test_websocket_gateway_works_without_gateway(gateway, watermark, options):
    assert isinstance(gateway, GatewayType)
    assert hasattr(gateway, "__GATEWAY_WATERMARK__") is watermark

    assert reflect.get_metadata_or_raise_exception(GATEWAY_WATERMARK, gateway) is True
    assert reflect.get_metadata_or_raise_exception(GATEWAY_OPTIONS, gateway) == options

    for key in GATEWAY_METADATA.keys:
        reflect.get_metadata_or_raise_exception(key, gateway)


def test_gateway_guard():
    assert reflect.get_metadata_or_raise_exception(
        GUARDS_KEY, SampleWithoutGateway
    ) == [GuardHttpBearerAuth]


def test_sub_message_building_works():
    @WebSocketGateway(path="/ws", namespace="/some-namespace")
    class SampleAGateway(GatewayBase):
        @subscribe_message
        def a_message(self):
            pass

    message_handlers = reflect.get_metadata_or_raise_exception(
        GATEWAY_MESSAGE_HANDLER_KEY, SampleAGateway
    )
    assert len(message_handlers) == 1
    assert get_name(message_handlers[0]) == "a_message"
    message = reflect.get_metadata_or_raise_exception(
        MESSAGE_METADATA, message_handlers[0]
    )
    assert message == "a_message"
    assert (
        reflect.get_metadata_or_raise_exception(
            CONTROLLER_CLASS_KEY, SampleAGateway().a_message
        )
        is SampleAGateway
    )


def test_sub_message_building_fails():
    with pytest.raises(Exception) as ex:

        @WebSocketGateway(path="/ws", namespace="/some-namespace")
        class SampleBGateway(GatewayBase):
            @subscribe_message
            @reflect.metadata(CONTROLLER_CLASS_KEY, "b_message")
            def b_message(self):
                pass

    assert (
        "SampleBGateway Gateway message handler tried to be processed more than once"
        in str(ex.value)
    )


def test_cant_use_gateway_decorator_on_function():
    with pytest.raises(Exception) as ex:

        @WebSocketGateway(path="/ws", namespace="/some-namespace")
        def sample_c_gateway():
            pass

    assert "WebSocketGateway is a class decorator" in str(ex.value)
