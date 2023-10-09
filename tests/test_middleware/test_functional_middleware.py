from ellar.common import IHostContext, Inject, Module, ModuleRouter, middleware
from ellar.core import ModuleBase
from ellar.core.middleware import FunctionBasedMiddleware
from ellar.reflect import asynccontextmanager
from ellar.testing import Test
from starlette.requests import Request
from starlette.responses import PlainTextResponse

mr = ModuleRouter()


@mr.get()
def homepage(request: Inject[Request]):
    if request.headers.get("modified_header"):
        return "homepage modified_header"

    if request.state.user:
        return request.state.user
    return "homepage"


@Module(routers=[mr])
class ModuleMiddleware(ModuleBase):
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
            request.state.user = {"username": "Ellar"}
        await call_next()

    @middleware()
    async def middleware_return_response(cls, context: IHostContext, call_next):
        request = context.switch_to_http_connection().get_request()
        if request.headers.get("ellar"):
            return PlainTextResponse("middleware_return_response returned a response")
        await call_next()


def test_middleware_modifying_response():
    tm = Test.create_test_module(modules=[ModuleMiddleware])
    client = tm.get_test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["modified-header"] == "Ellar"


def test_middleware_modifying_request():
    tm = Test.create_test_module(modules=[ModuleMiddleware])
    client = tm.get_test_client()

    response = client.get("/", headers={"set-user": "set"})
    assert response.status_code == 200
    assert response.json() == {"username": "Ellar"}


def test_middleware_returns_response():
    tm = Test.create_test_module(modules=[ModuleMiddleware])
    client = tm.get_test_client()

    response = client.get("/", headers={"ellar": "set"})
    assert response.status_code == 200
    assert response.text == "middleware_return_response returned a response"


def test_functional_middleware_skips_lifespan(test_client_factory):
    async def middleware_function(context: IHostContext, call_next):
        pass

    startup_complete = False
    cleanup_complete = False

    @asynccontextmanager
    async def lifespan(app):
        nonlocal startup_complete, cleanup_complete
        startup_complete = True
        yield
        cleanup_complete = True

    app = FunctionBasedMiddleware(
        Test.create_test_module(
            config_module={"DEFAULT_LIFESPAN_HANDLER": lifespan}
        ).create_application(),
        middleware_function,
    )

    with test_client_factory(app):
        assert startup_complete
        assert not cleanup_complete
