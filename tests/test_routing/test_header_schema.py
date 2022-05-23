from ellar.common import Header
from ellar.core import TestClientFactory
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object

from .sample import Data, Filter

tm = TestClientFactory.create_test_module()


@tm.app.Get("/test/header")
def header_params_schema(
    request,
    filters: Filter = Header(..., alias="well_not_work_for_schema_with_many_field"),
):
    return filters.dict()


@tm.app.Get("/test-mixed/header")
def header_params_mixed_schema(
    request,
    filters: Filter = Header(...),
    data: Data = Header(...),
):
    return dict(filters=filters.dict(), data=data.dict())


def test_header_request():
    client = tm.get_client()
    response = client.get(
        "/test/header",
        headers={"from": "1", "to": "2", "range": "20", "foo": "1", "range2": "50"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02+00:00",
        "from_datetime": "1970-01-01T00:00:01+00:00",
        "range": 20,
    }

    response = client.get(
        "/test/header", headers={"from": "1", "to": "2", "range": "21"}
    )
    assert response.status_code == 422


def test_request_mixed():
    client = tm.get_client()
    response = client.get(
        "/test-mixed/header",
        headers={
            "from": "1",
            "to": "2",
            "range": "20",
            "foo": "1",
            "range2": "50",
            "int": "3",
            "float": "1.6",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "filters": {
            "to_datetime": "1970-01-01T00:00:02+00:00",
            "from_datetime": "1970-01-01T00:00:01+00:00",
            "range": 20,
        },
        "data": {"an_int": 3, "a_float": 1.6},
    }

    response = client.get(
        "/test-mixed/header", headers={"from": "1", "to": "2", "range": "21"}
    )
    assert response.status_code == 422


def test_header_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(tm.app))
    params = document["paths"]["/test/header"]["get"]["parameters"]
    assert params == [
        {
            "required": False,
            "schema": {"title": "To", "type": "string", "format": "date-time"},
            "name": "to",
            "in": "header",
        },
        {
            "required": False,
            "schema": {"title": "From", "type": "string", "format": "date-time"},
            "name": "from",
            "in": "header",
        },
        {
            "required": False,
            "schema": {
                "allOf": [{"$ref": "#/components/schemas/Range"}],
                "default": 20,
            },
            "name": "range",
            "in": "header",
        },
    ]
