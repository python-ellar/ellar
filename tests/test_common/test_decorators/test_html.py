import pytest

from ellar.common import Controller, get, render, template_filter, template_global
from ellar.common.decorators.html import RenderDecoratorException
from ellar.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
    RESPONSE_OVERRIDE_KEY,
    TEMPLATE_FILTER_KEY,
    TEMPLATE_GLOBAL_KEY,
)
from ellar.core.connection import Request
from ellar.core.exceptions import ImproperConfiguration
from ellar.core.response.model import HTMLResponseModel
from ellar.core.templating import TemplateFunctionData
from ellar.reflect import reflect


def test_render_decorator_works():
    @render("index")
    def endpoint_render(request: Request):
        pass  # pragma: no cover

    response_override = reflect.get_metadata(RESPONSE_OVERRIDE_KEY, endpoint_render)
    assert isinstance(response_override, dict)
    html_response: HTMLResponseModel = response_override[200]
    assert isinstance(html_response, HTMLResponseModel)
    assert html_response.template_name == "index"


def test_render_decorator_wont_work_after_route_action_definition():
    @render("index")
    class Whatever:
        pass

    response_override = reflect.get_metadata(RESPONSE_OVERRIDE_KEY, Whatever)
    assert response_override is None


def test_render_decorator_raise_exception_for_invalid_template_name():
    with pytest.raises(
        AssertionError, match="Render Operation must invoked eg. @render()"
    ):

        @render
        def endpoint_render(request: Request):
            pass  # pragma: no cover


def test_render_decorator_uses_endpoint_name_as_template_name():
    @Controller
    class AController:
        @get("/endpoint_render")
        @render()
        def endpoint_render(self, request: Request):
            pass  # pragma: no cover

    a_controller_operations = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, AController
    )
    assert len(a_controller_operations) == 1
    endpoint_render_operation = a_controller_operations[0]
    response_override = reflect.get_metadata(
        RESPONSE_OVERRIDE_KEY, endpoint_render_operation.endpoint
    )
    html_response: HTMLResponseModel = response_override[200]

    assert isinstance(html_response, HTMLResponseModel)
    assert html_response.template_name == "endpoint_render"
    assert html_response.use_mvc


def test_render_decorator_fails_for_missing_template_name():
    with pytest.raises(
        RenderDecoratorException,
        match="template_name is required for function endpoints.",
    ):

        @render()
        def endpoint_render(request):
            pass  # pragma: no cover


def test_template_global_function_applies_template_global_key():
    @template_global()
    def global_function_test():
        pass  # pragma: no cover

    assert hasattr(global_function_test, TEMPLATE_GLOBAL_KEY)
    template_data: TemplateFunctionData = getattr(
        global_function_test, TEMPLATE_GLOBAL_KEY
    )
    assert template_data.func is global_function_test
    assert template_data.name == "global_function_test"


def test_template_global_function_fails_for_async_functions():
    with pytest.raises(
        ImproperConfiguration,
        match="TemplateGlobalCallable must be a non coroutine function",
    ):

        @template_global()
        async def global_function_test():
            pass  # pragma: no cover


def test_template_filter_function_applies_template_filter_key():
    @template_filter()
    def filter_function_test():
        pass  # pragma: no cover

    assert hasattr(filter_function_test, TEMPLATE_FILTER_KEY)
    template_data: TemplateFunctionData = getattr(
        filter_function_test, TEMPLATE_FILTER_KEY
    )
    assert template_data.func is filter_function_test
    assert template_data.name == "filter_function_test"


def test_template_filter_function_fails_for_async_functions():
    with pytest.raises(
        ImproperConfiguration,
        match="TemplateGlobalCallable must be a non coroutine function",
    ):

        @template_filter()
        async def filter_function_test():
            pass  # pragma: no cover
