from unittest.mock import MagicMock

import pytest
from ellar.common.constants import CONTROLLER_CLASS_KEY
from ellar.reflect import reflect
from ellar.socket_io.gateway import SocketOperationConnection


@reflect.metadata(CONTROLLER_CLASS_KEY, type("Custom", (), {}))
async def message_handler():
    pass


def test_gateway_controller_type():
    operation = SocketOperationConnection(
        event="an_event", server=MagicMock(), message_handler=message_handler
    )
    assert operation._controller_type is not None
    operation._controller_type = None
    assert operation.get_controller_type() is not None

    with pytest.raises(Exception, match=r"Operation must have a single control type."):
        reflect.delete_metadata(CONTROLLER_CLASS_KEY, message_handler)
        operation._controller_type = None

        operation.get_controller_type()
