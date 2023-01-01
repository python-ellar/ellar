import pytest

from ellar.common import Path, get
from ellar.core import TestClientFactory
from ellar.core.connection import Request
from ellar.core.exceptions import ImproperConfiguration
from ellar.core.routing import ModuleRouter
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object

from .sample import Filter, ListOfPrimitiveSchema, NonPrimitiveSchema

mr = ModuleRouter("")


@mr.get("/path-with-schema/{from}/{to}/{range}")
def path_params_schema(
    request: Request,
    filters: Filter = Path(..., alias="will_not_work_for_schema_with_many_field"),
):
    return filters.dict()


test_module = TestClientFactory.create_test_module(routers=(mr,))


def test_request():
    client = test_module.get_client()
    response = client.get("/path-with-schema/1/2/20")
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02+00:00",
        "from_datetime": "1970-01-01T00:00:01+00:00",
        "range": 20,
    }

    response = client.get("/path-with-schema/1/2/100")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["path", "range"],
                "msg": "value is not a valid enumeration member; permitted: 20, 50, 200",
                "type": "type_error.enum",
                "ctx": {"enum_values": [20, 50, 200]},
            }
        ]
    }


def test_schema():
    document = serialize_object(
        OpenAPIDocumentBuilder().build_document(test_module.app)
    )
    params = document["paths"]["/path-with-schema/{from}/{to}/{range}"]["get"][
        "parameters"
    ]
    assert params == [
        {
            "required": True,
            "schema": {"title": "To", "type": "string", "format": "date-time"},
            "name": "to",
            "in": "path",
        },
        {
            "required": True,
            "schema": {"title": "From", "type": "string", "format": "date-time"},
            "name": "from",
            "in": "path",
        },
        {
            "required": True,
            "schema": {"$ref": "#/components/schemas/Range"},
            "name": "range",
            "in": "path",
        },
    ]


def test_for_invalid_schema():
    with pytest.raises(ImproperConfiguration) as ex:

        @get("/{filter}")
        def invalid_path_parameter(path: NonPrimitiveSchema = Path()):
            pass

    assert (
        str(ex.value)
        == "Path params must be of one of the supported types. Only primitive types"
    )

    with pytest.raises(ImproperConfiguration) as ex:

        @get("/{int}/{float}")
        def invalid_path_parameter(path: ListOfPrimitiveSchema = Path()):
            pass

    assert (
        str(ex.value)
        == "Path params must be of one of the supported types. Only primitive types"
    )
