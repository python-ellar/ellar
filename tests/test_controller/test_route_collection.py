from typing import List

import pytest
from ellar.common import Version as version_decorator
from ellar.common import get, http_route, ws_route
from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_OPERATION_HANDLER_KEY,
)
from ellar.common.routing import (
    RouteCollection,
    RouteOperation,
    WebsocketRouteOperation,
)
from ellar.common.utils import generate_controller_operation_unique_id
from ellar.core.routing.helper import build_route_handler
from ellar.core.versioning import UrlPathAPIVersioning
from ellar.reflect import reflect
from ellar.testing import Test
from starlette.responses import JSONResponse
from starlette.routing import Host, Mount


class Configuration:
    VERSIONING_SCHEME = UrlPathAPIVersioning()


config_path = "tests.test_controller.test_route_collection:Configuration"


def create_route_operation(
    path: str, methods: List[str], versions: List[str] = None
) -> RouteOperation:
    if versions is None:
        versions = []

    @http_route(path, methods=methods)
    @version_decorator(*versions)
    def endpoint_sample():
        response = JSONResponse(
            content={"path": path, "methods": methods, "versioning": versions}
        )
        return response

    return build_route_handler(endpoint_sample)


def create_ws_route_operation(
    path: str, versions: List[str] = None
) -> WebsocketRouteOperation:
    if versions is None:
        versions = []

    @ws_route(path)
    @version_decorator(*versions)
    def endpoint_sample():
        response = JSONResponse(content={"path": path, "versioning": versions})
        return response

    return build_route_handler(endpoint_sample)


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


@pytest.mark.parametrize("collection_model", [RouteCollection])
def test_module_route_collection_for_same_path_but_different_version(collection_model):
    routes = collection_model()
    routes.extend(
        [
            create_route_operation("/sample", methods=["post"], versions=[]),
            create_route_operation("/sample", methods=["post"], versions=["1"]),
        ]
    )
    assert len(routes) == 2
    for route in routes:
        assert route.path == "/sample"

    tm = Test.create_test_module(config_module=config_path)
    tm.create_application().router.extend(routes)
    client = tm.get_test_client()

    response = client.post("/sample")
    assert response.status_code == 200
    assert response.json() == {"path": "/sample", "methods": ["post"], "versioning": []}

    response = client.post("/v1/sample")
    assert response.status_code == 200
    assert response.json() == {
        "path": "/sample",
        "methods": ["post"],
        "versioning": ["1"],
    }


@pytest.mark.parametrize("collection_model", [RouteCollection])
def test_module_route_collection_extend(collection_model):
    routes = collection_model()
    routes.extend(
        [
            create_route_operation("/sample", methods=["post"], versions=[]),
            create_route_operation("/sample", methods=["post"], versions=[]),
            create_route_operation("/sample", methods=["post"], versions=["1"]),
            create_ws_route_operation("/sample", versions=["1"]),
        ]
    )
    assert len(routes) == 4


@pytest.mark.parametrize("collection_model", [RouteCollection])
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


@pytest.mark.parametrize("collection_model", [RouteCollection])
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
    [(RouteCollection, "/sample")],
)
def test_module_route_collection_setitem_and_getitem(collection_model, expected_result):
    routes = collection_model()
    routes[0] = create_route_operation("/sample/1", methods=["post"], versions=[])
    routes[1] = create_route_operation("/sample", methods=["post"], versions=["1"])
    routes[2] = create_route_operation("/sample/2", methods=["post"], versions=[])

    # add unknown type
    routes[3] = type("MockRouteOperation", (), {})  # this will be ignored

    assert len(routes) == 3
    assert routes[0].path == expected_result


@pytest.mark.parametrize("collection_model", [RouteCollection])
def test_module_route_collection_for_same_path_different_method(
    collection_model, test_client_factory
):
    routes = collection_model()
    routes.append(create_route_operation("/sample", methods=["post"], versions=[]))
    routes.append(
        create_route_operation("/sample", methods=["post", "get"], versions=[])
    )

    assert len(routes) == 2

    tm = Test.create_test_module(config_module=config_path)
    tm.create_application().router.extend(routes)
    client = tm.get_test_client()

    response = client.get("/sample")
    assert response.status_code == 200
    assert response.json() == {
        "path": "/sample",
        "methods": ["post", "get"],
        "versioning": [],
    }

    response = client.post("/sample")
    assert response.status_code == 200
    assert response.json() == {"path": "/sample", "methods": ["post"], "versioning": []}


@pytest.mark.parametrize("collection_model", [RouteCollection])
def test_route_collection_create_control_type(collection_model):
    @get()
    def endpoint_once():
        pass

    assert reflect.get_metadata(CONTROLLER_CLASS_KEY, endpoint_once) is None
    operation = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, endpoint_once)

    collection_model([operation])
    assert not isinstance(
        reflect.get_metadata(CONTROLLER_CLASS_KEY, endpoint_once), list
    )

    collection_model([operation])
    assert not isinstance(
        reflect.get_metadata(CONTROLLER_CLASS_KEY, endpoint_once), list
    )
