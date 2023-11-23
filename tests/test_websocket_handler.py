import pytest
from ellar.common import Controller, Inject, ModuleRouter, WsBody, ws_route
from ellar.common.constants import CONTROLLER_OPERATION_HANDLER_KEY
from ellar.common.exceptions import (
    ImproperConfiguration,
    WebSocketRequestValidationError,
)
from ellar.common.routing.websocket import WebSocketExtraHandler
from ellar.reflect import reflect
from ellar.testing import Test
from starlette.websockets import WebSocket, WebSocketState

from .schema import Item

router = ModuleRouter("/router")


@router.ws_route("/ws-with-handler", use_extra_handler=True)
async def websocket_with_handler(
    websocket: Inject[WebSocket], query: str, data: Item = WsBody()
):
    assert query == "my-query"
    await websocket.send_json(data.dict())
    await websocket.close()


@router.ws_route.connect(websocket_with_handler)
async def websocket_with_handler_connect(websocket: WebSocket):
    await websocket.accept()


@router.ws_route.disconnect(websocket_with_handler)
async def websocket_with_handler_disconnect(websocket: WebSocket, code: int):
    # await websocket.close(code=code)
    assert websocket.client_state == WebSocketState.DISCONNECTED


@router.ws_route("/ws")
async def websocket_without_handler(websocket: Inject[WebSocket], query: str):
    assert query == "my-query"
    await websocket.accept()
    message = await websocket.receive_text()
    await websocket.send_json({"message": f"Thanks. {message}"})
    await websocket.close()


@Controller("/controller")
class WebsocketController:
    @ws_route("/ws-with-handler", use_extra_handler=True)
    async def websocket_with_handler_c(
        self, websocket: Inject[WebSocket], query: str, data: Item = WsBody()
    ):
        assert query == "my-query"
        await websocket.send_json(data.dict())
        await websocket.close()

    @ws_route.connect(websocket_with_handler_c)
    async def websocket_with_handler_connect(self, websocket: WebSocket):
        await websocket.accept()

    @ws_route.disconnect(websocket_with_handler_c)
    async def websocket_with_handler_disconnect(self, websocket: WebSocket, code: int):
        # await websocket.close(code=code)
        assert websocket.client_state == WebSocketState.DISCONNECTED

    @ws_route("/ws")
    async def websocket_without_handler_c(
        self, websocket: Inject[WebSocket], query: str
    ):
        assert query == "my-query"
        await websocket.accept()
        message = await websocket.receive_text()
        await websocket.send_json({"message": f"Thanks. {message}"})
        await websocket.close()


tm = Test.create_test_module(routers=[router], controllers=(WebsocketController,))
client = tm.get_test_client()


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
    with pytest.raises(AssertionError):
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
    with pytest.raises(WebSocketRequestValidationError):
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
    tm = Test.create_test_module()
    with pytest.raises(
        ImproperConfiguration,
        match=r"`WsBody` should only be used when `use_extra_handler` flag is set to True in WsRoute",
    ):

        @router.ws_route("/ws-with-handler", use_extra_handler=False)
        async def websocket_with_handler(
            websocket: Inject[WebSocket], query: str, data: Item = WsBody()
        ):
            pass

        tm.create_application().router.append(websocket_with_handler)


def test_websocket_endpoint_on_connect():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True)
        async def ws(self, websocket: Inject[WebSocket]):
            pass

        @ws_route.connect(ws)
        async def on_connect(self, websocket):
            assert websocket["subprotocols"] == ["soap", "wamp"]
            await websocket.accept(subprotocol="wamp")

    _client = Test.create_test_module(controllers=(WebSocketSample,)).get_test_client()
    with _client.websocket_connect("/ws/", subprotocols=["soap", "wamp"]) as websocket:
        assert websocket.accepted_subprotocol == "wamp"


def test_websocket_endpoint_on_receive_bytes():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding="bytes")
        async def ws(self, websocket: Inject[WebSocket], data: bytes = WsBody()):
            await websocket.send_bytes(b"Message bytes was: " + data)

    _client = Test.create_test_module(controllers=(WebSocketSample,)).get_test_client()
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
        async def ws(self, websocket: Inject[WebSocket], data=WsBody()):
            await websocket.send_json({"message": data})

    _client = Test.create_test_module(controllers=(WebSocketSample,)).get_test_client()

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
        async def ws(self, websocket: Inject[WebSocket], data=WsBody()):
            await websocket.send_json({"message": data}, mode="binary")

    _client = Test.create_test_module(controllers=(WebSocketSample,)).get_test_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_json({"hello": "world"}, mode="binary")
        data = websocket.receive_json(mode="binary")
        assert data == {"message": {"hello": "world"}}


def test_websocket_endpoint_on_receive_text():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding="text")
        async def ws(self, websocket: Inject[WebSocket], data: str = WsBody()):
            await websocket.send_text(f"Message text was: {data}")

    _client = Test.create_test_module(controllers=(WebSocketSample,)).get_test_client()

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
        async def ws(self, websocket: Inject[WebSocket], data: str = WsBody()):
            await websocket.send_text(f"Message text was: {data}")

    _client = Test.create_test_module(controllers=(WebSocketSample,)).get_test_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_text("Hello, world!")
        _text = websocket.receive_text()
        assert _text == "Message text was: Hello, world!"


def test_websocket_endpoint_on_disconnect():
    @Controller("/ws")
    class WebSocketSample:
        @ws_route(use_extra_handler=True, encoding=None)
        async def ws(self, websocket: Inject[WebSocket], data: str = WsBody()):
            await websocket.send_text(f"Message text was: {data}")

        @ws_route.disconnect(ws)
        async def on_disconnect(self, websocket: WebSocket, close_code):
            assert close_code == 1001
            await websocket.close(code=close_code)

    _client = Test.create_test_module(controllers=(WebSocketSample,)).get_test_client()

    with _client.websocket_connect("/ws/") as websocket:
        websocket.send_text("Hello, world!")
        websocket.close(code=1001)


def test_ws_route_connect_raise_exception_for_invalid_type():
    with pytest.raises(
        Exception,
        match="Invalid type. Please make sure you passed the websocket handler.",
    ):

        @router.ws_route.connect(ModuleRouter)
        def some_example_connect():
            pass


def test_ws_route_connect_raise_exception_for_invalid_operation():
    with pytest.raises(
        Exception,
        match="Invalid type. Please make sure you passed the websocket handler.",
    ):

        @router.ws_route.connect(websocket_with_handler_connect)
        def some_example_connect():
            pass


def test_add_websocket_handler_raise_exception_for_wrong_handler_name():
    websocket_operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, websocket_with_handler
    )
    with pytest.raises(Exception) as ex:
        websocket_operation.add_websocket_handler(
            handler_name="mycustomname", handler=websocket_with_handler_connect
        )
    assert (
        str(ex.value)
        == "Invalid Handler Name. Handler Name must be in ['encoding', 'on_receive', 'on_connect', 'on_disconnect']"
    )
    websocket_operation.add_websocket_handler(
        handler_name="on_receive", handler=websocket_with_handler_connect
    )


def test_websocket_handler_fails_for_invalid_handlers():
    a_type = type("AType", (), {})
    with pytest.raises(ValueError):

        @ws_route(extra_handler_type=a_type)
        def invalid_ws_route():
            pass

    with pytest.raises(ValueError):

        @ws_route(extra_handler_type=a_type())
        def invalid_ws_route_case_2():
            pass

    @ws_route(extra_handler_type=WebSocketExtraHandler)
    def valid_ws_route():
        pass
