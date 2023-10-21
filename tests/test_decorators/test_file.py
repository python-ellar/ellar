import pytest
from ellar.common import Controller, Inject, file, get
from ellar.common.constants import (
    CONTROLLER_OPERATION_HANDLER_KEY,
    RESPONSE_OVERRIDE_KEY,
)
from ellar.common.responses.models import (
    FileResponseModel,
    ResponseModelField,
    StreamingResponseModel,
)
from ellar.core import Request
from ellar.reflect import reflect


def test_file_decorator_works():
    @file(media_type="text/javascript")
    def endpoint_file(request: Inject[Request]):
        """ignore"""

    response_override = reflect.get_metadata(RESPONSE_OVERRIDE_KEY, endpoint_file)
    assert isinstance(response_override, dict)
    file_response: FileResponseModel = response_override[200]
    assert isinstance(file_response, FileResponseModel)
    assert file_response.media_type == "text/javascript"
    assert isinstance(file_response.get_init_kwargs_schema(), ResponseModelField)


def test_file_streaming_decorator_works():
    @file(media_type="text/javascript", streaming=True)
    def endpoint_file(request: Inject[Request]):
        """ignore"""

    response_override = reflect.get_metadata(RESPONSE_OVERRIDE_KEY, endpoint_file)
    assert isinstance(response_override, dict)
    file_response: StreamingResponseModel = response_override[200]
    assert isinstance(file_response, StreamingResponseModel)
    assert file_response.media_type == "text/javascript"


def test_render_decorator_raise_exception_for_invalid_template_name():
    with pytest.raises(AssertionError, match="File decorator must invoked eg. @file()"):

        @file
        def endpoint_file(request: Inject[Request]):
            """ignore"""


def test_file_decorator_wont_work_after_route_action_definition():
    @file()
    class Whatever:
        pass

    response_override = reflect.get_metadata(RESPONSE_OVERRIDE_KEY, Whatever)
    assert response_override is None


def test_file_decorator_uses_endpoint_name_as_template_name():
    @Controller
    class AFileController:
        @get("/endpoint_file")
        @file(media_type="text/javascript")
        def endpoint_file(self, request: Inject[Request]):
            """ignore"""

    a_controller_operations = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, AFileController
    )
    assert len(a_controller_operations) == 1
    endpoint_render_operation = a_controller_operations[0]
    response_override = reflect.get_metadata(
        RESPONSE_OVERRIDE_KEY, endpoint_render_operation.endpoint
    )

    file_response: FileResponseModel = response_override[200]
    assert isinstance(file_response, FileResponseModel)
    assert file_response.media_type == "text/javascript"
    assert isinstance(file_response.get_init_kwargs_schema(), ResponseModelField)


def test_file_stream_decorator_uses_endpoint_name_as_template_name():
    @Controller
    class AStreamFileController:
        @get("/endpoint_file")
        @file(media_type="text/javascript", streaming=True)
        def endpoint_file(self, request: Inject[Request]):
            """ignore"""

    a_controller_operations = reflect.get_metadata(
        CONTROLLER_OPERATION_HANDLER_KEY, AStreamFileController
    )
    assert len(a_controller_operations) == 1
    endpoint_render_operation = a_controller_operations[0]
    response_override = reflect.get_metadata(
        RESPONSE_OVERRIDE_KEY, endpoint_render_operation.endpoint
    )

    file_response: StreamingResponseModel = response_override[200]
    assert isinstance(file_response, StreamingResponseModel)
    assert file_response.media_type == "text/javascript"
