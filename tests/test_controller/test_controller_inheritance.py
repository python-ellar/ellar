import pytest
from ellar.app import AppFactory
from ellar.common import Controller, get, ws_route
from ellar.common.constants import (
    CONTROLLER_CLASS_KEY,
    CONTROLLER_OPERATION_HANDLER_KEY,
)
from ellar.core.router_builders import ControllerRouterBuilder
from ellar.reflect import reflect


class ControllerImplementationBase:
    @get("/sample")
    def some_example(self):
        pass

    @ws_route("/sample")
    def some_example_ws(self):
        pass


@Controller(prefix="/items/{orgID:int}", name="override_name")
class MyController(ControllerImplementationBase):
    pass


def test_inheritance_fails():
    with pytest.raises(Exception) as ex:

        @Controller
        class NewController(MyController):
            pass

    assert "`@Controller` decorated classes does not support inheritance. " in str(ex)


def test_control_type_with_more_than_one_type_fails():
    @Controller
    class AnotherSampleController:
        @get()
        def endpoint_once(self):
            pass

    ControllerRouterBuilder.build(AnotherSampleController)

    reflect.define_metadata(
        CONTROLLER_CLASS_KEY,
        None,
        AnotherSampleController().endpoint_once,
    )
    operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, AnotherSampleController().endpoint_once
    )

    with pytest.raises(Exception, match=r"Operation must have a single control type."):
        operation._controller_type = None
        ControllerRouterBuilder.build(AnotherSampleController)


def test_controller_raise_exception_for_controller_operation_without_controller_class(
    test_client_factory,
):
    @Controller("/abcd")
    class Another2SampleController:
        @get("/test")
        def endpoint_once(self):
            pass

    app = AppFactory.create_app(controllers=(Another2SampleController,))
    reflect.delete_metadata(
        CONTROLLER_CLASS_KEY, Another2SampleController().endpoint_once
    )
    operation = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, Another2SampleController().endpoint_once
    )
    client = test_client_factory(app)

    with pytest.raises(Exception, match=r"Operation must have a single control type"):
        operation._controller_type = None
        client.get("/abcd/test")


def test_cant_build_operation_route_twice():
    @Controller("/abcd")
    class Another2SampleController:
        @get("/test")
        @reflect.metadata(CONTROLLER_CLASS_KEY, "b_message")
        def endpoint_once(self):
            pass

    with pytest.raises(
        Exception,
        match=r"Controller route function can not be reused once its under a `@Controller` decorator.",
    ):
        ControllerRouterBuilder.build(Another2SampleController)
