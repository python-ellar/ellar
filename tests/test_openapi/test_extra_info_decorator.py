import pytest
from ellar.app import AppFactory
from ellar.common import serialize_object
from ellar.common.compatible import AttributeDict
from ellar.common.exceptions import ImproperConfiguration
from ellar.core.connection import Request
from ellar.openapi import OpenAPIDocumentBuilder, api_info
from ellar.openapi.constants import OPENAPI_OPERATION_KEY
from ellar.reflect import reflect


@api_info(
    summary="Endpoint Summary",
    description="Endpoint Description",
    deprecated=False,
    operation_id="4524d-z23zd-453ed-2342e",
    tags=["endpoint", "endpoint-25"],
)
def endpoint(request: Request):
    pass  # pragma: no cover


def test_openapi_sets_endpoint_meta():
    open_api_data = reflect.get_metadata(OPENAPI_OPERATION_KEY, endpoint)
    assert isinstance(open_api_data, AttributeDict)
    assert open_api_data.summary == "Endpoint Summary"
    assert open_api_data.description == "Endpoint Description"
    assert open_api_data.deprecated is False
    assert open_api_data.operation_id == "4524d-z23zd-453ed-2342e"
    assert open_api_data.tags == ["endpoint", "endpoint-25"]


def test_invalid_api_info_decorator_setup():
    with pytest.raises(ImproperConfiguration):

        @api_info(
            operation_id="4524d-z23zd-453ed-2342e",
            tags="endpoint",
        )
        def endpoint(request: Request):
            pass  # pragma: no cover


def test_api_info_extra_keys():
    app = AppFactory.create_app()

    @app.router.get()
    @api_info(operation_id="4524d-z23zd-453ed-2342e", xyz="xyz", abc="abc")
    def endpoint_1(request: Request):
        pass

    open_api_data = reflect.get_metadata(OPENAPI_OPERATION_KEY, endpoint_1)
    assert open_api_data == {
        "operation_id": "4524d-z23zd-453ed-2342e",
        "summary": None,
        "description": None,
        "deprecated": None,
        "tags": None,
        "xyz": "xyz",
        "abc": "abc",
    }

    document = OpenAPIDocumentBuilder().build_document(app)
    data = serialize_object(document)
    assert data["paths"]["/"] == {
        "get": {
            "operationId": "4524d-z23zd-453ed-2342e",
            "responses": {
                "200": {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "title": "Response Model",
                            }
                        }
                    },
                }
            },
            "xyz": "xyz",
            "abc": "abc",
        }
    }
