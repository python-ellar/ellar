import pytest
from ellar.common import Controller, ControllerBase, get, http_route, ws_route
from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_OPERATION_HANDLER_KEY,
)
from ellar.core.routing import ControllerRouterFactory
from ellar.di import has_binding, is_decorated_with_injectable
from ellar.reflect import reflect

from .sample import SampleController


@Controller(prefix="/items/{orgID:int}", name="override_name")
class SomeController:
    def __init__(self, a: str):
        self.a = a

    @get("/sample")
    def some_example(self):
        pass

    @get("/sample")
    def some_example_3(self):
        # some_example_3 overrides `sample_example` OPERATION since its the same 'path' and 'method'
        pass

    @http_route("/sample", methods=["get"])
    def some_example_4(self):
        # some_example_4 overrides `sample_example_3` OPERATION since its the same 'path' and 'method'
        pass

    @http_route("/sample", methods=["get", "post"])
    def some_example_5(self):
        # `sample_example_4 - get` overrides `sample_example_5 - get` RUNTIME CALL in that order
        # And '/sample' POST call will be handled here
        pass

    @ws_route("/sample")
    def some_example_ws(self):
        pass

    @ws_route("/sample")
    def some_example_ws_2(self):
        # `some_example_ws_2` overrides `some_example_ws` OPERATION
        pass


def test_controller_routes_has_controller_type():
    routes = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, SampleController)
    assert routes

    for route in routes:
        controller_type = reflect.get_metadata(CONTROLLER_CLASS_KEY, route.endpoint)
        assert controller_type == SampleController


def test_controller_computed_properties():
    assert isinstance(SampleController, type) and issubclass(
        SampleController, ControllerBase
    )
    ControllerRouterFactory.build(SampleController)

    assert is_decorated_with_injectable(SampleController)
    assert not has_binding(SampleController)

    @Controller(
        prefix="/items/{orgID:int}",
    )
    class SomeControllerB(ControllerBase):
        def __init__(self, a: str):
            self.a = a

    ControllerRouterFactory.build(SomeControllerB)
    assert is_decorated_with_injectable(SomeControllerB)
    assert has_binding(SomeControllerB)


@pytest.mark.parametrize(
    "controller_type, prefix, name",
    [
        (SampleController, "/prefix", "sample"),
        (
            SomeController,
            "/items/{orgID:int}",
            "override_name",
        ),
    ],
)
def test_controller_url_reverse(controller_type, prefix, name):
    router = ControllerRouterFactory.build(controller_type)
    for route in router.routes:
        reversed_path = router.url_path_for(f"{name}:{route.name}")
        assert reversed_path == router.path_format.replace("/{path}", route.path)
