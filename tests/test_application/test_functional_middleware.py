from starlette.requests import Request
from starlette.responses import PlainTextResponse

from ellar.common import Module, ModuleRouter, middleware
from ellar.core import TestClientFactory
from ellar.core.context import IHostContext

mr = ModuleRouter()


@mr.get()
def homepage(request: Request):
    if request.headers.get("modified_header"):
        return "homepage modified_header"

    if request.state.user:
        return request.state.user
    return "homepage"


@Module(routers=[mr])
class ModuleMiddleware:
    @middleware()
    async def middleware_modify_response(cls, context: IHostContext, call_next):
        response = context.switch_to_http_connection().get_response()
        response.headers.setdefault("modified-header", "Ellar")
        await call_next()

    @middleware()
    async def middleware_modify_request(cls, context: IHostContext, call_next):
        request = context.switch_to_http_connection().get_request()
        request.state.user = None
        if request.headers.get("set-user"):
            request.state.user = dict(username="Ellar")
        await call_next()

    @middleware()
    async def middleware_return_response(cls, context: IHostContext, call_next):
        request = context.switch_to_http_connection().get_request()
        if request.headers.get("ellar"):
            return PlainTextResponse("middleware_return_response returned a response")
        await call_next()


def test_middleware_modifying_response():
    tm = TestClientFactory.create_test_module_from_module(ModuleMiddleware)
    client = tm.get_client()

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["modified-header"] == "Ellar"


def test_middleware_modifying_request():
    tm = TestClientFactory.create_test_module_from_module(ModuleMiddleware)
    client = tm.get_client()

    response = client.get("/", headers={"set-user": "set"})
    assert response.status_code == 200
    assert response.json() == {"username": "Ellar"}


def test_middleware_returns_response():
    tm = TestClientFactory.create_test_module_from_module(ModuleMiddleware)
    client = tm.get_client()

    response = client.get("/", headers={"ellar": "set"})
    assert response.status_code == 200
    assert response.text == "middleware_return_response returned a response"
