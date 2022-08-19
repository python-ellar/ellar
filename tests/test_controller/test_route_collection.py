from typing import List

import pytest
from starlette.responses import JSONResponse
from starlette.routing import Host, Mount, Router, compile_path

from ellar.core import Config
from ellar.core.middleware import RequestVersioningMiddleware
from ellar.core.routing import RouteOperation, WebsocketRouteOperation
from ellar.core.routing.router import ModuleRouteCollection, RouteCollection
from ellar.core.versioning import UrlPathAPIVersioning
from ellar.helper import generate_controller_operation_unique_id

config = Config(VERSIONING_SCHEME=UrlPathAPIVersioning())


def create_app(router):
    return RequestVersioningMiddleware(router, debug=False, config=config)


class MockRouteOperation(RouteOperation):
    def __init__(self, path: str, methods: List[str], versions: List[str] = []):
        self.path = path
        self.path_regex, self.path_format, self.param_convertors = compile_path(
            self.path
        )
        self.methods = [method.upper() for method in methods]
        self._versioning = versions

    def endpoint(self):
        pass

    async def app(self, scope, receive, send) -> None:
        response = JSONResponse(
            content=dict(
                path=self.path, methods=self.methods, versioning=self._versioning
            )
        )
        await response(scope, receive, send)

    def get_allowed_version(self):
        return self._versioning


class MockWebsocketRouteOperation(WebsocketRouteOperation):
    def __init__(self, path: str, versions: List[str] = []):
        self.path = path
        self._versioning = versions

    async def app(self, scope, receive, send) -> None:
        response = JSONResponse(
            content=dict(
                path=self.path, methods=self.methods, versioning=self._versioning
            )
        )
        await response(scope, receive, send)

    def get_allowed_version(self):
        return self._versioning


class MockHostRouteOperation(Host):
    def asgi_app(self, scope, receive, send):
        pass

    def __init__(self, host: str, name: str = None):
        super().__init__(host=host, name=name, app=self.asgi_app)


class MockMountRouteOperation(Mount):
    def asgi_app(self, scope, receive, send):
        pass

    def __init__(self, path: str, name: str = None):
        super().__init__(path=path, name=name, app=self.asgi_app)


@pytest.mark.parametrize("collection_model", [ModuleRouteCollection, RouteCollection])
def test_module_route_collection_for_same_path_but_different_version(
    collection_model, test_client_factory
):
    routes = collection_model()
    routes.append(MockRouteOperation("/sample", methods=["post"], versions=[]))
    routes.append(MockRouteOperation("/sample", methods=["post"], versions=["1"]))
    assert len(routes) == 2
    for route in routes:
        assert route.path == "/sample"

    client = test_client_factory(create_app(Router(routes=routes)))
    response = client.post("/sample")
    assert response.status_code == 200
    assert response.json() == {"path": "/sample", "methods": ["POST"], "versioning": []}

    response = client.post("/v1/sample")
    assert response.status_code == 200
    assert response.json() == {
        "path": "/sample",
        "methods": ["POST"],
        "versioning": ["1"],
    }


@pytest.mark.parametrize("collection_model", [ModuleRouteCollection, RouteCollection])
def test_module_route_collection_extend(collection_model):
    routes = collection_model()
    routes.extend(
        [
            MockRouteOperation("/sample", methods=["post"], versions=[]),
            MockRouteOperation("/sample", methods=["post"], versions=[]),
            MockRouteOperation("/sample", methods=["post"], versions=["1"]),
            MockWebsocketRouteOperation("/sample", versions=["1"]),
        ]
    )
    assert len(routes) == 3


@pytest.mark.parametrize("collection_model", [ModuleRouteCollection, RouteCollection])
def test_module_route_collection_host(collection_model):

    routes = collection_model()
    routes.append(MockHostRouteOperation("{subdomain}.example.org"))
    _hash = generate_controller_operation_unique_id(
        path="{subdomain}.example.org",
        methods=["MockHostRouteOperation"],
        versioning=["no_versioning"],
    )
    assert _hash in routes._routes
    routes.append(MockHostRouteOperation("{subdomain}.example.org", name="mock_host"))
    _hash = generate_controller_operation_unique_id(
        path="{subdomain}.example.org",
        methods=["MockHostRouteOperation", "mock_host"],
        versioning=["no_versioning"],
    )
    assert _hash in routes._routes


@pytest.mark.parametrize("collection_model", [ModuleRouteCollection, RouteCollection])
def test_module_route_collection_mount(collection_model):
    routes = collection_model()
    routes.append(MockMountRouteOperation("/mount"))
    _hash = generate_controller_operation_unique_id(
        path="/mount",
        methods=["MockMountRouteOperation"],
        versioning=["no_versioning"],
    )
    assert _hash in routes._routes
    routes.append(MockMountRouteOperation("/mount", name="mock_mount"))
    _hash = generate_controller_operation_unique_id(
        path="/mount",
        methods=["MockMountRouteOperation", "mock_mount"],
        versioning=["no_versioning"],
    )
    assert _hash in routes._routes


@pytest.mark.parametrize(
    "collection_model, expected_result",
    [(ModuleRouteCollection, "/sample/1"), (RouteCollection, "/sample")],
)
def test_module_route_collection_setitem_and_getitem(collection_model, expected_result):
    routes = collection_model()
    routes[0] = MockRouteOperation("/sample/1", methods=["post"], versions=[])
    routes[1] = MockRouteOperation("/sample", methods=["post"], versions=["1"])
    routes[2] = MockRouteOperation("/sample/2", methods=["post"], versions=[])

    # add unknown type
    routes[3] = type("MockRouteOperation", (), {})  # this will be ignored

    assert len(routes) == 3
    assert routes[0].path == expected_result


@pytest.mark.parametrize("collection_model", [ModuleRouteCollection, RouteCollection])
def test_module_route_collection_for_same_path_different_method(
    collection_model, test_client_factory
):
    routes = collection_model()
    routes.append(MockRouteOperation("/sample", methods=["post"], versions=[]))
    routes.append(MockRouteOperation("/sample", methods=["post", "get"], versions=[]))

    assert len(routes) == 2

    client = test_client_factory(create_app(Router(routes=routes)))
    response = client.get("/sample")
    assert response.status_code == 200
    assert response.json() == {
        "path": "/sample",
        "methods": ["POST", "GET"],
        "versioning": [],
    }

    response = client.post("/sample")
    assert response.status_code == 200
    assert response.json() == {"path": "/sample", "methods": ["POST"], "versioning": []}
