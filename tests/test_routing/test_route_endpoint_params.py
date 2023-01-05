from starlette.requests import (
    HTTPConnection as StarletteHTTPConnection,
    Request as StarletteRequest,
)
from starlette.responses import Response as StarletteResponse
from starlette.websockets import WebSocket as StarletteWebSocket

from ellar.common import Context, Http, Req, Res, Ws
from ellar.core import ExecutionContext, TestClientFactory
from ellar.core.connection import (
    HTTPConnection as EllarHTTPConnection,
    Request as EllarRequest,
    WebSocket as EllarWebSocket,
)
from ellar.core.context import IExecutionContext
from ellar.core.routing import ModuleRouter

router = ModuleRouter()


@router.get("/starlette-request")
def get_requests(request: StarletteRequest, req=Req()):
    assert isinstance(request, EllarRequest)  # True
    assert isinstance(req, EllarRequest)
    return req == request


@router.get("/ellar-context")
def get_requests(context_1: IExecutionContext, context_2=Context()):
    assert isinstance(context_1, ExecutionContext)
    return context_1 == context_2


@router.get("/starlette-connection")
def get_connections(connection: StarletteHTTPConnection, connection_2=Http()):
    assert isinstance(connection, EllarHTTPConnection)  # True
    assert isinstance(connection_2, EllarHTTPConnection)
    return connection == connection_2


@router.get("/starlette-response")
def get_responses(response: StarletteResponse, response_2=Res()):
    assert isinstance(response, StarletteResponse)  # True
    assert isinstance(response_2, StarletteResponse)
    return response == response_2


@router.ws_route("/starlette-websocket")
async def get_websockets(websocket: StarletteWebSocket, ws=Ws()):
    assert isinstance(ws, EllarWebSocket)  # True
    assert isinstance(websocket, EllarWebSocket)
    await ws.accept()
    await ws.send_json(ws == websocket)
    await ws.close()


tm = TestClientFactory.create_test_module(routers=[router])
client = tm.get_client()


def test_get_connections():
    response = client.get("/starlette-connection")
    assert response.status_code == 200
    assert response.json() is True


def test_get_request():
    response = client.get("/starlette-request")
    assert response.status_code == 200
    assert response.json() is True


def test_get_context():
    response = client.get("/ellar-context")
    assert response.status_code == 200
    assert response.json() is True


def test_get_response():
    response = client.get("/starlette-response")
    assert response.status_code == 200
    assert response.json() is True


def test_get_websocket():
    with client.websocket_connect("/starlette-websocket") as session:
        data = session.receive_json()
        assert data is True
