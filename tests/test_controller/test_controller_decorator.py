import pytest

from ellar.common import Get, HttpRoute, WsRoute
from ellar.core import ControllerBase
from ellar.core.routing import ControllerDecorator, ControllerRouter, ControllerType
from ellar.di import has_binding, is_decorated_with_injectable

from .sample import SampleController


class SomeController(ControllerBase):
    def __init__(self, a: str):
        self.a = a

    @Get("/sample")
    def some_example(self):
        pass

    @Get("/sample")
    def some_example_3(self):
        # some_example_3 overrides `sample_example` OPERATION since its the same 'path' and 'method'
        pass

    @HttpRoute("/sample", methods=["get"])
    def some_example_4(self):
        # some_example_4 overrides `sample_example_3` OPERATION since its the same 'path' and 'method'
        pass

    @HttpRoute("/sample", methods=["get", "post"])
    def some_example_5(self):
        # `sample_example_4 - Get` overrides `sample_example_5 - Get` RUNTIME CALL in that order
        # And '/sample' POST call will be handled here
        pass

    @WsRoute("/sample")
    def some_example_ws(self):
        pass

    @WsRoute("/sample")
    def some_example_ws_2(self):
        # `some_example_ws_2` overrides `some_example_ws` OPERATION
        pass


def test_get_controller_type():
    assert isinstance(SampleController, ControllerDecorator)
    assert SampleController.get_controller_type()
    assert isinstance(SampleController.get_controller_type(), ControllerType)

    with pytest.raises(AssertionError):
        ControllerDecorator().get_controller_type()

    with pytest.raises(AssertionError):
        ControllerDecorator().get_router()


def test_controller_computed_properties():
    assert isinstance(SampleController, ControllerDecorator)
    controller_type = SampleController.get_controller_type()

    assert is_decorated_with_injectable(controller_type)
    assert not has_binding(controller_type)
    assert SampleController.get_meta() == {
        "tag": "sample",
        "description": None,
        "external_doc_description": None,
        "external_doc_url": None,
        "path": "/prefix",
        "name": "sample",
        "version": set(),
        "guards": [],
        "include_in_schema": True,
    }
    new_controller = ControllerDecorator(
        prefix="/items/{orgID:int}",
        tag="Item",
        description="Some Controller",
        external_doc_url="https://test.com",
        external_doc_description="Find out more here",
    )(SomeController)
    assert new_controller.get_meta() == {
        "tag": "Item",
        "description": "Some Controller",
        "external_doc_description": "Find out more here",
        "external_doc_url": "https://test.com",
        "path": "/items/{orgID:int}",
        "name": "some",
        "version": set(),
        "guards": [],
        "include_in_schema": True,
    }
    assert is_decorated_with_injectable(new_controller.get_controller_type())
    assert has_binding(new_controller.get_controller_type())


@pytest.mark.parametrize(
    "controller_decorator, routes_count",
    [
        (SampleController, 2),
        (
            ControllerDecorator(
                prefix="/items/{orgID:int}",
            )(SomeController),
            3,
        ),
    ],
)
def test_get_mount(controller_decorator, routes_count):
    assert isinstance(controller_decorator, ControllerDecorator)
    controller_router = controller_decorator.get_router()
    assert isinstance(controller_router, ControllerRouter)
    assert len(controller_router.routes) == routes_count


def test_tag_configuration_controller_decorator():
    new_controller = ControllerDecorator(
        prefix="/items/{orgID:int}", name="override_name", tag="new_tag"
    )(SomeController)
    assert new_controller.get_meta()["tag"] == "new_tag"
    assert new_controller.get_meta()["name"] == "override_name"

    # defaults to controller name
    new_controller = ControllerDecorator(
        prefix="/items/{orgID:int}",
    )(SomeController)
    assert new_controller.get_meta()["tag"] == "some"
    assert new_controller.get_meta()["name"] == "some"

    new_controller = ControllerDecorator(prefix="/items/{orgID:int}", tag="new_tag")(
        SomeController
    )
    assert new_controller.get_meta()["tag"] == "new_tag"
    assert new_controller.get_meta()["name"] == "some"


@pytest.mark.parametrize(
    "controller_decorator, tag, prefix, name",
    [
        (SampleController, "sample", "/prefix", "sample"),
        (
            ControllerDecorator(
                prefix="/items/{orgID:int}", name="override_name", tag="new_tag"
            )(SomeController),
            "new_tag",
            "/items/{orgID:int}",
            "override_name",
        ),
    ],
)
def test_build_routes(controller_decorator, tag, prefix, name):
    controller_decorator.build_routes()
    router = controller_decorator.get_router()

    for route in router.routes:
        assert name in route.name
        assert prefix in route.path
        if "WS" not in route.methods:
            assert tag in route.get_meta().openapi.tags
    assert router.controller_type is controller_decorator.get_controller_type()
