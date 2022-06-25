from ellar.common import Cookie
from ellar.core import TestClientFactory
from ellar.core.routing import ModuleRouter
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object

from .sample import Data, Filter

router = ModuleRouter("")


@router.get("/test/cookie")
def cookie_params_schema(
    request,
    filters: Filter = Cookie(..., alias="will_not_work_for_schema_with_many_field"),
):
    return filters.dict()


@router.get("/test-mixed/cookie")
def cookie_params_mixed_schema(
    request,
    filters: Filter = Cookie(...),
    data: Data = Cookie(...),
):
    return dict(filters=filters.dict(), data=data.dict())


tm = TestClientFactory.create_test_module(routers=(router,))


def test_cookie_request():
    client = tm.get_client()
    response = client.get(
        "/test/cookie",
        cookies={"from": "1", "to": "2", "range": "20", "foo": "1", "range2": "50"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02+00:00",
        "from_datetime": "1970-01-01T00:00:01+00:00",
        "range": 20,
    }

    response = client.get(
        "/test/cookie", cookies={"from": "1", "to": "2", "range": "21"}
    )
    assert response.status_code == 422


def test_cookie_request_mixed():
    client = tm.get_client()
    response = client.get(
        "/test-mixed/cookie",
        cookies={
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
        "/test-mixed/cookie", cookies={"from": "1", "to": "2", "range": "21"}
    )
    assert response.status_code == 422


def test_cookie_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(tm.app))
    params = document["paths"]["/test/cookie"]["get"]["parameters"]
    assert params == [
        {
            "required": False,
            "schema": {"title": "To", "type": "string", "format": "date-time"},
            "name": "to",
            "in": "cookie",
        },
        {
            "required": False,
            "schema": {"title": "From", "type": "string", "format": "date-time"},
            "name": "from",
            "in": "cookie",
        },
        {
            "required": False,
            "schema": {
                "allOf": [{"$ref": "#/components/schemas/Range"}],
                "default": 20,
            },
            "name": "range",
            "in": "cookie",
        },
    ]
