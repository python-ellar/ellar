import pytest
from ellar.common import Inject, WsBody, get, ws_route
from ellar.common.exceptions.validation import (
    RequestValidationError,
    WebSocketRequestValidationError,
)
from ellar.core import WebSocket
from ellar.testing import Test
from pydantic.error_wrappers import ErrorWrapper

from .exception_runner import ExceptionRunner

test_module = Test.create_test_module()

_exception_runner = ExceptionRunner(RequestValidationError)


@get("/exception-validation")
def exception_http():
    _exception_runner.run()


@ws_route("/exception-Ws", use_extra_handler=False)
async def exception_ws(websocket: Inject[WebSocket]):
    _exception_runner.run()


@ws_route("/exception-Ws-2", use_extra_handler=True)
async def exception_ws_2(websocket: Inject[WebSocket], data: WsBody[dict]):
    assert data == {"hello": "world"}
    _exception_runner.run()


test_module.create_application().router.extend(
    [exception_http, exception_ws_2, exception_ws]
)
client = test_module.get_test_client()


def test_request_validation_error():
    global _exception_runner
    _exception_runner = ExceptionRunner(
        RequestValidationError,
        errors=[
            ErrorWrapper(Exception("Invalid Request"), loc="body"),
            ErrorWrapper(Exception("Invalid Request"), loc="form"),
            ErrorWrapper(Exception("Invalid Request"), loc="model"),
        ],
    )
    response = client.get("/exception-validation")
    data = response.json()
    assert response.status_code == 422
    assert data == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "Invalid Request",
                "type": "value_error.exception",
            },
            {
                "loc": ["form"],
                "msg": "Invalid Request",
                "type": "value_error.exception",
            },
            {
                "loc": ["model"],
                "msg": "Invalid Request",
                "type": "value_error.exception",
            },
        ]
    }


def test_websocket_validation_error():
    global _exception_runner
    _exception_runner = ExceptionRunner(
        WebSocketRequestValidationError,
        errors=[
            ErrorWrapper(Exception("Invalid Request"), loc="body"),
            ErrorWrapper(Exception("Invalid Request"), loc="form"),
            ErrorWrapper(Exception("Invalid Request"), loc="model"),
        ],
    )
    with pytest.raises(WebSocketRequestValidationError) as wex:
        with client.websocket_connect("/exception-Ws") as websocket:
            websocket.send_json({"hello": "world"})
    assert wex.value.errors() == [
        {"loc": ("body",), "msg": "Invalid Request", "type": "value_error.exception"},
        {"loc": ("form",), "msg": "Invalid Request", "type": "value_error.exception"},
        {"loc": ("model",), "msg": "Invalid Request", "type": "value_error.exception"},
    ]


def test_websocket_validation_error_2():
    global _exception_runner
    _exception_runner = ExceptionRunner(
        WebSocketRequestValidationError,
        errors=[
            ErrorWrapper(Exception("Invalid Request"), loc="body"),
            ErrorWrapper(Exception("Invalid Request"), loc="form"),
            ErrorWrapper(Exception("Invalid Request"), loc="model"),
        ],
    )
    with pytest.raises(WebSocketRequestValidationError) as wex:
        with client.websocket_connect("/exception-Ws-2") as websocket:
            websocket.send_json({"hello": "world"})
    assert wex.value.errors() == [
        {"loc": ("body",), "msg": "Invalid Request", "type": "value_error.exception"},
        {"loc": ("form",), "msg": "Invalid Request", "type": "value_error.exception"},
        {"loc": ("model",), "msg": "Invalid Request", "type": "value_error.exception"},
    ]
