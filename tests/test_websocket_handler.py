import pytest
from starlette.websockets import WebSocket

from ellar.common import ModuleRouter, WsBody
from ellar.core import TestClientFactory
from ellar.core.exceptions import ImproperConfiguration

from .schema import Item

router = ModuleRouter("/")


@router.ws_route("/ws-with-handler", use_extra_handler=True)
async def websocket_with_handler(
    websocket: WebSocket, query: str, data: Item = WsBody()
):
    assert query == "my-query"
    await websocket.send_json(data.dict())
    await websocket.close()


@websocket_with_handler.connect
async def websocket_with_handler_connect(websocket: WebSocket):
    await websocket.accept()


@router.ws_route("/ws")
async def websocket_without_handler(websocket: WebSocket, query: str):
    assert query == "my-query"
    await websocket.accept()
    message = await websocket.receive_text()
    await websocket.send_json({"message": f"Thanks. {message}"})
    await websocket.close()


tm = TestClientFactory.create_test_module(routers=[router])
client = tm.get_client()


def test_websocket_with_handler_works():
    with client.websocket_connect("/ws-with-handler?query=my-query") as session:
        session.send_json(Item(name="Ellar", price=23.34, tax=1.2).dict())
        message = session.receive_json()
        assert message == {
            "name": "Ellar",
            "description": None,
            "price": 23.34,
            "tax": 1.2,
        }


def test_websocket_with_handler_fails_for_invalid_input():
    with pytest.raises(Exception):
        with client.websocket_connect("/ws-with-handler?query=my-query") as session:
            session.send_json({"framework": "Ellar is awesome"})
            message = session.receive_json()
    assert message == {
        "code": 1008,
        "errors": [
            {
                "loc": ["body", "name"],
                "msg": "field required",
                "type": "value_error.missing",
            },
            {
                "loc": ["body", "price"],
                "msg": "field required",
                "type": "value_error.missing",
            },
        ],
    }


def test_websocket_with_handler_fails_for_missing_route_parameter():
    with pytest.raises(Exception):
        with client.websocket_connect("/ws-with-handler") as session:
            session.send_json(Item(name="Ellar", price=23.34, tax=1.2).dict())
            message = session.receive_json()
    assert message == {
        "code": 1008,
        "errors": [
            {
                "loc": ["query", "query"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ],
    }


def test_plain_websocket_route():
    with client.websocket_connect("/ws?query=my-query") as websocket:
        websocket.send_text("Ellar")
        message = websocket.receive_json()
        assert message == {"message": "Thanks. Ellar"}


def test_websocket_setup_fails_when_using_body_without_handler():
    with pytest.raises(
        ImproperConfiguration,
        match=r"`WsBody` should only be used when `use_extra_handler` flag is set to True in WsRoute",
    ):

        @router.ws_route("/ws-with-handler", use_extra_handler=False)
        async def websocket_with_handler(
            websocket: WebSocket, query: str, data: Item = WsBody()
        ):
            pass
