from starlette.requests import Request
from starlette.responses import PlainTextResponse

from ellar.common import IHostContext, Module, ModuleRouter, middleware
from ellar.core import App, Config, ModuleBase
from ellar.core.middleware import FunctionBasedMiddleware
from ellar.di import EllarInjector
from ellar.reflect import asynccontextmanager
from ellar.testing import Test

mr = ModuleRouter()


@mr.get()
def homepage(request: Request):
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
            request.state.user = dict(username="Ellar")
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
        App(config=Config(), injector=EllarInjector(), lifespan=lifespan),
        middleware_function,
    )

    with test_client_factory(app):
        assert startup_complete
        assert not cleanup_complete
