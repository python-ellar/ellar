from ellar.common import Controller, get, ws_route
from ellar.common.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
)
from ellar.core.router_builders import ControllerRouterBuilder
from ellar.reflect import reflect


class ControllerBaseMixin:
    @get("/sample")
    def some_example(self):
        pass

    @ws_route("/sample")
    def some_example_ws(self):
        pass


@Controller(prefix="/items/{orgID:int}", name="override_name")
class MyController(ControllerBaseMixin):
    pass


def test_inheritance_works():
    # with pytest.raises(Exception) as ex:

    @Controller
    class NewController(MyController):
        @get("/sample-another")
        def some_example_another(self):
            pass

    ControllerRouterBuilder.build(NewController)
    routes = reflect.get_metadata(CONTROLLER_OPERATION_HANDLER_KEY, NewController)
    assert len(routes) == 3

    for route in routes:
        controller_type = route.get_controller_type()
        assert controller_type == NewController


def test_type_method_can_still_reflect_function_metadata():
    @Controller
    class AnotherSampleController:
        @get()
        def endpoint_once(self):
            pass

    ControllerRouterBuilder.build(AnotherSampleController)
    assert reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, AnotherSampleController().endpoint_once
    )
