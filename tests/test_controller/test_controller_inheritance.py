import pytest

from ellar.common import Controller, get, ws_route
from ellar.constants import CONTROLLER_CLASS_KEY
from ellar.core.routing.router.module import controller_router_factory
from ellar.reflect import reflect


class ControllerImplementationBase:
    @get("/sample")
    def some_example(self):
        pass

    @ws_route("/sample")
    def some_example_ws(self):
        pass


@Controller(prefix="/items/{orgID:int}", name="override_name", tag="new_tag")
class MyController(ControllerImplementationBase):
    pass


def test_inheritance_fails():
    with pytest.raises(Exception) as ex:

        @Controller
        class NewController(ControllerImplementationBase):
            pass

    assert (
        "NewController Controller route tried to be processed more than once."
        in str(ex)
    )


def test_control_type_with_more_than_one_type_fails():
    @Controller
    class AnotherSampleController:
        @get()
        def endpoint_once(self):
            pass

    reflect.define_metadata(
        CONTROLLER_CLASS_KEY,
        type("slme", (), {}),
        AnotherSampleController.endpoint_once,
    )

    with pytest.raises(Exception, match=r"Operation must have a single control type."):
        controller_router_factory(AnotherSampleController)
