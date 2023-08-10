from ellar.auth.session import ISessionStrategy
from ellar.auth.session.strategy import SessionClientStrategy
from ellar.common import (
    Context,
    Host,
    Http,
    IExecutionContext,
    ModuleRouter,
    Provide,
    Req,
    Res,
    Session,
    Ws,
)
from ellar.core import Config, ExecutionContext
from ellar.core.connection import (
    HTTPConnection as EllarHTTPConnection,
)
from ellar.core.connection import (
    Request as EllarRequest,
)
from ellar.core.connection import (
    WebSocket as EllarWebSocket,
)
from ellar.testing import Test
from starlette.requests import (
    HTTPConnection as StarletteHTTPConnection,
)
from starlette.requests import (
    Request as StarletteRequest,
)
from starlette.responses import Response as StarletteResponse
from starlette.websockets import WebSocket as StarletteWebSocket

router = ModuleRouter()


@router.get("/starlette-request")
def get_requests_case_1(request: StarletteRequest, req=Req()):
    assert isinstance(request, EllarRequest)  # True
    assert isinstance(req, EllarRequest)
    return req == request


@router.get("/others")
def get_requests_case_2(session=Session(), host=Host(), config=Provide(Config)):
    assert isinstance(config, Config)  # True
    assert host == "testclient"
    assert isinstance(session, dict) and len(session) == 0
    return True


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


SECRET_KEY = "ellar_cf303596-e51a-441a-ba67-5da42dbffb07"
tm = Test.create_test_module(
    routers=[router],
    config_module={
        "SECRET_KEY": SECRET_KEY,
    },
).override_provider(ISessionStrategy, use_class=SessionClientStrategy)
client = tm.get_test_client()


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


def test_other_route_function_parameter():
    response = client.get("/others")
    assert response.status_code == 200
    assert response.json() is True


def test_get_websocket():
    with client.websocket_connect("/starlette-websocket") as session:
        data = session.receive_json()
        assert data is True
