import pytest
from starlette.websockets import WebSocket, WebSocketState

from ellar.common import Controller, ModuleRouter, WsBody, ws_route
from ellar.core import TestClientFactory
from ellar.core.exceptions import ImproperConfiguration

from .schema import Item

router = ModuleRouter("/router")


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


@websocket_with_handler.disconnect
async def websocket_with_handler_connect(websocket: WebSocket, code: int):
    # await websocket.close(code=code)
    assert websocket.client_state == WebSocketState.DISCONNECTED


@router.ws_route("/ws")
async def websocket_without_handler(websocket: WebSocket, query: str):
    assert query == "my-query"
    await websocket.accept()
    message = await websocket.receive_text()
    await websocket.send_json({"message": f"Thanks. {message}"})
    await websocket.close()


@Controller("/controller")
class WebsocketController:
    @ws_route("/ws-with-handler", use_extra_handler=True)
    async def websocket_with_handler_c(
        self, websocket: WebSocket, query: str, data: Item = WsBody()
    ):
        assert query == "my-query"
        await websocket.send_json(data.dict())
        await websocket.close()

    @websocket_with_handler_c.connect
    async def websocket_with_handler_connect(self, websocket: WebSocket):
        await websocket.accept()

    @websocket_with_handler_c.disconnect
    async def websocket_with_handler_connect(self, websocket: WebSocket, code: int):
        # await websocket.close(code=code)
        assert websocket.client_state == WebSocketState.DISCONNECTED

    @ws_route("/ws")
    async def websocket_without_handler_c(self, websocket: WebSocket, query: str):
        assert query == "my-query"
        await websocket.accept()
        message = await websocket.receive_text()
        await websocket.send_json({"message": f"Thanks. {message}"})
        await websocket.close()


tm = TestClientFactory.create_test_module(
    routers=[router], controllers=(WebsocketController,)
)
client = tm.get_client()


@pytest.mark.parametrize("prefix", ["/router", "/controller"])
def test_websocket_with_handler_works(prefix):
    with client.websocket_connect(
        f"{prefix}/ws-with-handler?query=my-query"
    ) as session:
        session.send_json(Item(name="Ellar", price=23.34, tax=1.2).dict())
        message = session.receive_json()
        assert message == {
            "name": "Ellar",
            "description": None,
            "price": 23.34,
            "tax": 1.2,
        }


@pytest.mark.parametrize("prefix", ["/router", "/controller"])
def test_websocket_with_handler_fails_for_invalid_input(prefix):
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"{prefix}/ws-with-handler?query=my-query"
        ) as session:
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


@pytest.mark.parametrize("prefix", ["/router", "/controller"])
def test_websocket_with_handler_fails_for_missing_route_parameter(prefix):
    with pytest.raises(Exception):
        with client.websocket_connect(f"{prefix}/ws-with-handler") as session:
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


@pytest.mark.parametrize("prefix", ["/router", "/controller"])
def test_plain_websocket_route(prefix):
    with client.websocket_connect(f"{prefix}/ws?query=my-query") as websocket:
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


def test_websocket_endpoint_on_connect():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True)
        async def ws(self, websocket: WebSocket):
            pass

        @ws.connect
        async def on_connect(self, websocket):
            assert websocket["subprotocols"] == ["soap", "wamp"]
            await websocket.accept(subprotocol="wamp")

    _client = TestClientFactory.create_test_module(
        controllers=(WebSocketSample,)
    ).get_client()
    with _client.websocket_connect("/ws/", subprotocols=["soap", "wamp"]) as websocket:
        assert websocket.accepted_subprotocol == "wamp"


def test_websocket_endpoint_on_receive_bytes():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding="bytes")
        async def ws(self, websocket: WebSocket, data: bytes = WsBody()):
            await websocket.send_bytes(b"Message bytes was: " + data)

    _client = TestClientFactory.create_test_module(
        controllers=(WebSocketSample,)
    ).get_client()
    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_bytes(b"Hello, world!")
        _bytes = websocket.receive_bytes()
        assert _bytes == b"Message bytes was: Hello, world!"

    with pytest.raises(RuntimeError):
        with _client.websocket_connect("/ws/") as websocket:
            websocket.send_text("Hello world")


def test_websocket_endpoint_on_receive_json():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding="json")
        async def ws(self, websocket: WebSocket, data=WsBody()):
            await websocket.send_json({"message": data})

    _client = TestClientFactory.create_test_module(
        controllers=(WebSocketSample,)
    ).get_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_json({"hello": "world"})
        data = websocket.receive_json()
        assert data == {"message": {"hello": "world"}}

    with pytest.raises(RuntimeError):
        with _client.websocket_connect("/ws/") as websocket:
            websocket.send_text("Hello world")


def test_websocket_endpoint_on_receive_json_binary():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding="json")
        async def ws(self, websocket: WebSocket, data=WsBody()):
            await websocket.send_json({"message": data}, mode="binary")

    _client = TestClientFactory.create_test_module(
        controllers=(WebSocketSample,)
    ).get_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_json({"hello": "world"}, mode="binary")
        data = websocket.receive_json(mode="binary")
        assert data == {"message": {"hello": "world"}}


def test_websocket_endpoint_on_receive_text():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding="text")
        async def ws(self, websocket: WebSocket, data: str = WsBody()):
            await websocket.send_text(f"Message text was: {data}")

    _client = TestClientFactory.create_test_module(
        controllers=(WebSocketSample,)
    ).get_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_text("Hello, world!")
        _text = websocket.receive_text()
        assert _text == "Message text was: Hello, world!"

    with pytest.raises(RuntimeError):
        with _client.websocket_connect("/ws/") as websocket:
            websocket.send_bytes(b"Hello world")


def test_websocket_endpoint_on_default():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding=None)
        async def ws(self, websocket: WebSocket, data: str = WsBody()):
            await websocket.send_text(f"Message text was: {data}")

    _client = TestClientFactory.create_test_module(
        controllers=(WebSocketSample,)
    ).get_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_text("Hello, world!")
        _text = websocket.receive_text()
        assert _text == "Message text was: Hello, world!"


def test_websocket_endpoint_on_disconnect():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding=None)
        async def ws(self, websocket: WebSocket, data: str = WsBody()):
            await websocket.send_text(f"Message text was: {data}")

        @ws.disconnect
        async def on_disconnect(self, websocket: WebSocket, close_code):
            assert close_code == 1001
            await websocket.close(code=close_code)

    _client = TestClientFactory.create_test_module(
        controllers=(WebSocketSample,)
    ).get_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_text("Hello, world!")
        websocket.close(code=1001)
