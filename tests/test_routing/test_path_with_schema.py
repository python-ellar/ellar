import pytest
from ellar.common import Inject, ModuleRouter, Path, get, serialize_object
from ellar.common.exceptions import ImproperConfiguration
from ellar.core.connection import Request
from ellar.core.routing.helper import build_route_handler
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

from .sample import Filter, ListOfPrimitiveSchema, NonPrimitiveSchema

mr = ModuleRouter("")


@mr.get("/path-with-schema/{from}/{to}/{range}")
def path_params_schema(
    request: Inject[Request],
    filters: Filter = Path(..., alias="will_not_work_for_schema_with_many_field"),
):
    return filters.dict()


test_module = Test.create_test_module(routers=(mr,))
app = test_module.create_application()


def test_request():
    client = test_module.get_test_client()
    response = client.get("/path-with-schema/1/2/20")
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02Z",
        "from_datetime": "1970-01-01T00:00:01Z",
        "range": 20,
    }

    response = client.get("/path-with-schema/1/2/100")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "ctx": {"expected": "20, 50 or 200"},
                "input": 100,
                "loc": ["path", "range"],
                "msg": "Input should be 20, 50 or 200",
                "type": "enum",
            }
        ]
    }


def test_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    params = document["paths"]["/path-with-schema/{from}/{to}/{range}"]["get"][
        "parameters"
    ]
    assert params == [
        {
            "required": True,
            "schema": {"type": "string", "title": "To"},
            "name": "to",
            "in": "path",
        },
        {
            "required": True,
            "schema": {"type": "string", "title": "From"},
            "name": "from",
            "in": "path",
        },
        {
            "required": False,
            "schema": {
                "allOf": [{"$ref": "#/components/schemas/Range"}],
                "title": "Range",
                "default": 20,
                "repr": True,
            },
            "name": "range",
            "in": "path",
        },
    ]


def test_for_invalid_schema():
    with pytest.raises(ImproperConfiguration) as ex:

        @get("/{filter}")
        def invalid_path_parameter(path: NonPrimitiveSchema = Path()):
            pass

        build_route_handler(invalid_path_parameter)

    assert (
        str(ex.value)
        == "Path params must be of one of the supported types. Only primitive types"
    )

    with pytest.raises(ImproperConfiguration) as ex:

        @get("/{int}/{float}")
        def invalid_path_parameter(path: ListOfPrimitiveSchema = Path()):
            pass

        build_route_handler(invalid_path_parameter)

    assert (
        str(ex.value)
        == "Path params must be of one of the supported types. Only primitive types"
    )
