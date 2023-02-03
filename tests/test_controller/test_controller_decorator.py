import pytest

from ellar.common import Controller, get, http_route, ws_route
from ellar.constants import CONTROLLER_CLASS_KEY, CONTROLLER_OPERATION_HANDLER_KEY
from ellar.core import ControllerBase
from ellar.core.routing.router.module import controller_router_factory
from ellar.di import has_binding, is_decorated_with_injectable
from ellar.reflect import reflect

from .sample import SampleController


@Controller(prefix="/items/{orgID:int}", name="override_name", tag="new_tag")
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
    router = controller_router_factory(SampleController)

    assert is_decorated_with_injectable(SampleController)
    assert not has_binding(SampleController)

    assert router.get_meta() == {
        "tag": "sample",
        "external_doc_description": None,
        "description": None,
        "external_doc_url": None,
    }

    @Controller(
        prefix="/items/{orgID:int}",
        tag="Item",
        description="Some Controller",
        external_doc_url="https://test.com",
        external_doc_description="Find out more here",
    )
    class SomeControllerB(ControllerBase):
        def __init__(self, a: str):
            self.a = a

    router = controller_router_factory(SomeControllerB)
    assert router.get_meta() == {
        "tag": "Item",
        "description": "Some Controller",
        "external_doc_description": "Find out more here",
        "external_doc_url": "https://test.com",
    }
    assert is_decorated_with_injectable(SomeControllerB)
    assert has_binding(SomeControllerB)


def test_tag_configuration_controller_decorator():
    new_controller = Controller(
        prefix="/items/{orgID:int}", name="override_name", tag="new_tag"
    )(type("SomeControllerX", (ControllerBase,), {}))
    router = controller_router_factory(new_controller)
    assert router.get_meta()["tag"] == "new_tag"
    assert router.name == "override_name"

    # defaults to controller name
    new_controller = Controller(
        prefix="/items/{orgID:int}",
    )(type("SomeControllerY", (ControllerBase,), {}))
    router = controller_router_factory(new_controller)
    assert router.get_meta()["tag"] == "somey"
    assert router.name == "somey"

    new_controller = Controller(prefix="/items/{orgID:int}", tag="new_tag")(
        type("SomeControllerZ", (ControllerBase,), {})
    )
    router = controller_router_factory(new_controller)
    assert router.get_meta()["tag"] == "new_tag"
    assert router.name == "somez"


@pytest.mark.parametrize(
    "controller_type, tag, prefix, name",
    [
        (SampleController, "sample", "/prefix", "sample"),
        (
            SomeController,
            "new_tag",
            "/items/{orgID:int}",
            "override_name",
        ),
    ],
)
def test_controller_url_reverse(controller_type, tag, prefix, name):
    router = controller_router_factory(controller_type)
    for route in router.routes:
        reversed_path = router.url_path_for(f"{name}:{route.name}")
        assert reversed_path == router.path_format.replace("/{path}", route.path)
