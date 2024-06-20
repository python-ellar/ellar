import json

import pytest
from ellar.app.services import EllarAppService
from ellar.common import IHostContextFactory
from ellar.common.exceptions import HostContextException
from ellar.core import ApplicationContext, Config, current_injector
from ellar.core.middleware import ServerErrorMiddleware
from ellar.di import EllarInjector
from ellar.threading.sync_worker import execute_async_context_manager

from ..injector_module import Configuration, DummyModule


async def assert_service_provider_app(scope, receive, send):
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    _config_repr = repr(current_injector.get(Configuration))
    str_provider = current_injector.get(str)
    await send(
        {
            "type": "http.response.body",
            "body": json.dumps(
                {"str": str_provider, "configuration": _config_repr}
            ).encode(),
        }
    )


async def assert_iexecute_context_app(scope, receive, send):
    host_context_factory: IHostContextFactory = current_injector.get(
        IHostContextFactory
    )
    host_context = host_context_factory.create_context(scope, receive, send)

    with pytest.raises(HostContextException):
        host_context.switch_to_websocket()

    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": json.dumps({"message": "execution context work"}).encode(),
        }
    )


async def assert_iexecute_context_app_websocket(scope, receive, send):
    host_context_factory: IHostContextFactory = current_injector.get(
        IHostContextFactory
    )
    host_context = host_context_factory.create_context(scope, receive, send)

    websocket = host_context.switch_to_websocket().get_client()
    assert current_injector is host_context.get_service_provider()

    with pytest.raises(HostContextException):
        host_context.switch_to_http_connection().get_request()

    with pytest.raises(HostContextException):
        host_context.switch_to_http_connection().get_response()

    await websocket.accept()
    await websocket.send_text("Hello, world!")
    await websocket.close()


def test_di_middleware(test_client_factory):
    injector_ = EllarInjector()
    injector_.container.install(DummyModule)
    asgi_app = ServerErrorMiddleware(
        assert_service_provider_app, debug=False, injector=injector_
    )
    EllarAppService(injector_, config=Config()).register_core_services()

    with execute_async_context_manager(ApplicationContext(injector_)):
        client = test_client_factory(asgi_app)
        response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["str"] == "Ellar"
    assert data["configuration"] == repr(injector_.get(Configuration))


def test_di_middleware_execution_context_initialization(test_client_factory):
    injector_ = EllarInjector()
    asgi_app = ServerErrorMiddleware(
        assert_iexecute_context_app, debug=False, injector=injector_
    )
    EllarAppService(injector_, config=Config()).register_core_services()
    with execute_async_context_manager(ApplicationContext(injector_)):
        client = test_client_factory(asgi_app)
        response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "execution context work"


def test_di_middleware_execution_context_initialization_websocket(test_client_factory):
    injector_ = EllarInjector()
    asgi_app = ServerErrorMiddleware(
        assert_iexecute_context_app_websocket, debug=False, injector=injector_
    )
    EllarAppService(injector_, config=Config()).register_core_services()
    client = test_client_factory(asgi_app)
    with execute_async_context_manager(ApplicationContext(injector_)):
        with client.websocket_connect("/") as session:
            text = session.receive_text()
            assert text == "Hello, world!"
