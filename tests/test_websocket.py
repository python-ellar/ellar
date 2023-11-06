import sys

import anyio
import pytest
from ellar.app import AppFactory
from ellar.common import Header, Inject, ws_route
from starlette import status
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState


def test_websocket_url(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.send_json({"url": str(websocket.url)})
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/123?a=abc") as websocket:
        data = websocket.receive_json()
        assert data == {"url": "ws://testserver/123?a=abc"}


def test_websocket_binary_json(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        message = await websocket.receive_json(mode="binary")
        await websocket.send_json(message, mode="binary")
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/123?a=abc") as websocket:
        websocket.send_json({"test": "data"}, mode="binary")
        data = websocket.receive_json(mode="binary")
        assert data == {"test": "data"}


def test_websocket_query_params(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket], a: str, b: str) -> None:
        await websocket.accept()
        await websocket.send_json({"params": {"a": a, "b": b}})
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/?a=abc&b=456") as websocket:
        data = websocket.receive_json()
        assert data == {"params": {"a": "abc", "b": "456"}}


@pytest.mark.skipif(
    any(module in sys.modules for module in ("brotli", "brotlicffi")),
    reason='urllib3 includes "br" to the "accept-encoding" headers.',
)
def test_websocket_headers(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(
        websocket: Inject[WebSocket], user_agent: str = Header()
    ) -> None:
        headers = dict(websocket.headers)
        assert user_agent == headers["user-agent"]
        await websocket.accept()
        await websocket.send_json({"headers": headers})
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        expected_headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "connection": "upgrade",
            "host": "testserver",
            "user-agent": "testclient",
            "sec-websocket-key": "testserver==",
            "sec-websocket-version": "13",
        }
        data = websocket.receive_json()
        assert data == {"headers": expected_headers}


def test_websocket_port(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.send_json({"port": websocket.url.port})
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("ws://example.com:123/123?a=abc") as websocket:
        data = websocket.receive_json()
        assert data == {"port": 123}


def test_websocket_send_and_receive_text(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        data = await websocket.receive_text()
        await websocket.send_text("Message was: " + data)
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_text("Hello, world!")
        data = websocket.receive_text()
        assert data == "Message was: Hello, world!"


def test_websocket_send_and_receive_bytes(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        data = await websocket.receive_bytes()
        await websocket.send_bytes(b"Message was: " + data)
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_bytes(b"Hello, world!")
        data = websocket.receive_bytes()
        assert data == b"Message was: Hello, world!"


def test_websocket_send_and_receive_json(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        _data = await websocket.receive_json()
        await websocket.send_json({"message": _data})
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"hello": "world"})
        data = websocket.receive_json()
        assert data == {"message": {"hello": "world"}}


def test_websocket_iter_text(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        async for _data in websocket.iter_text():
            await websocket.send_text("Message was: " + _data)

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_text("Hello, world!")
        data = websocket.receive_text()
        assert data == "Message was: Hello, world!"


def test_websocket_iter_bytes(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        async for data_ in websocket.iter_bytes():
            await websocket.send_bytes(b"Message was: " + data_)

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_bytes(b"Hello, world!")
        data = websocket.receive_bytes()
        assert data == b"Message was: Hello, world!"


def test_websocket_iter_json(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        async for data_ in websocket.iter_json():
            await websocket.send_json({"message": data_})

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"hello": "world"})
        data = websocket.receive_json()
        assert data == {"message": {"hello": "world"}}


def test_websocket_concurrency_pattern(test_client_factory):
    stream_send, stream_receive = anyio.create_memory_object_stream()

    async def reader(websocket):
        async with stream_send:
            async for data in websocket.iter_json():
                await stream_send.send(data)

    async def writer(websocket):
        async with stream_receive:
            async for message in stream_receive:
                await websocket.send_json(message)

    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        async with anyio.create_task_group() as task_group:
            task_group.start_soon(reader, websocket)
            await writer(websocket)
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.send_json({"hello": "world"})
        data = websocket.receive_json()
        assert data == {"hello": "world"}


def test_client_close(test_client_factory):
    close_code = None

    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        nonlocal close_code
        await websocket.accept()
        try:
            await websocket.receive_text()
        except WebSocketDisconnect as exc:
            close_code = exc.code

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        websocket.close(code=status.WS_1001_GOING_AWAY)
    assert close_code == status.WS_1001_GOING_AWAY


def test_application_close(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.close(status.WS_1001_GOING_AWAY)

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_text()
        assert exc.value.code == status.WS_1001_GOING_AWAY


def test_rejected_connection(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.close(status.WS_1001_GOING_AWAY)

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/"):
            pass  # pragma: nocover
    assert exc.value.code == status.WS_1001_GOING_AWAY


def test_subprotocol(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        assert websocket["subprotocols"] == ["soap", "wamp"]
        await websocket.accept(subprotocol="wamp")
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/", subprotocols=["soap", "wamp"]) as websocket:
        assert websocket.accepted_subprotocol == "wamp"


def test_additional_headers(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept(headers=[(b"additional", b"header")])
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        assert websocket.extra_headers == [(b"additional", b"header")]


def test_no_additional_headers(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        assert websocket.extra_headers == []


def test_websocket_exception(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        raise AssertionError()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(AssertionError):
        with client.websocket_connect("/123?a=abc"):
            pass  # pragma: nocover


def test_duplicate_close(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.close()
        await websocket.close()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_duplicate_disconnect(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        message = await websocket.receive()
        assert message["type"] == "websocket.disconnect"
        message = await websocket.receive()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/") as websocket:
            websocket.close()


def test_websocket_close_reason(test_client_factory) -> None:
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.close(code=status.WS_1001_GOING_AWAY, reason="Going Away")

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with client.websocket_connect("/") as websocket:
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_text()
        assert exc.value.code == status.WS_1001_GOING_AWAY
        assert exc.value.reason == "Going Away"


def test_send_json_invalid_mode(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.send_json({}, mode="invalid")

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_receive_json_invalid_mode(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.receive_json(mode="invalid")

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_receive_text_before_accept(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.receive_text()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_receive_bytes_before_accept(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.receive_bytes()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_receive_json_before_accept(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.receive_json()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_send_before_accept(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.send({"type": "websocket.send"})

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_send_wrong_message_type(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.send({"type": "websocket.accept"})
        await websocket.send({"type": "websocket.accept"})

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/"):
            pass  # pragma: nocover


def test_receive_before_accept(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        websocket.client_state = WebSocketState.CONNECTING
        await websocket.receive()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/") as websocket:
            websocket.send({"type": "websocket.send"})


def test_receive_wrong_message_type(test_client_factory):
    @ws_route("/{path:path}")
    async def ws_function(websocket: Inject[WebSocket]) -> None:
        await websocket.accept()
        await websocket.receive()

    app = AppFactory.create_app()
    app.router.append(ws_function)

    client = test_client_factory(app)
    with pytest.raises(RuntimeError):
        with client.websocket_connect("/") as websocket:
            websocket.send({"type": "websocket.connect"})
