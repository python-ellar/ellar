import pytest
from ellar.common import Header, Inject, ModuleRouter, get, serialize_object
from ellar.common.exceptions import ImproperConfiguration
from ellar.core.connection import Request
from ellar.core.routing.helper import build_route_handler
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

from .sample import Data, Filter, NonPrimitiveSchema

mr = ModuleRouter("")


@mr.get("/test/header")
def header_params_schema(
    request: Inject[Request],
    filters: Filter = Header(..., alias="will_not_work_for_schema_with_many_field"),
):
    return filters.dict()


@mr.get("/test-mixed/header")
def header_params_mixed_schema(
    request: Inject[Request],
    filters: Header[Filter],
    data: Header[Data],
):
    return {"filters": filters.dict(), "data": data.dict()}


@mr.post("/header-alias")
def header_with_alias(
    request: Inject[Request],
    qty: Header[str, Header.P(alias="aliasQty")],
):
    return {"aliasQty": qty}


tm = Test.create_test_module(routers=(mr,))
app = tm.create_application()


def test_header_with_alias():
    client = tm.get_test_client()
    response = client.post(
        "/header-alias",
        json={},
        headers={
            "aliasQty": "234",
        },
    )

    assert response.json() == {
        "aliasQty": "234",
    }

    response = client.post(
        "/header-alias",
        headers={
            "qty": "234",
        },
    )
    assert response.status_code == 422
    json = response.json()
    assert json == {
        "detail": [
            {
                "loc": ["header", "aliasQty"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ]
    }


def test_header_request():
    client = tm.get_test_client()
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
    client = tm.get_test_client()
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
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    params = document["paths"]["/test/header"]["get"]["parameters"]
    assert params == [
        {
            "required": False,
            "schema": {
                "title": "To",
                "type": "string",
                "format": "date-time",
                "include_in_schema": True,
            },
            "name": "to",
            "in": "header",
        },
        {
            "required": False,
            "schema": {
                "title": "From",
                "type": "string",
                "format": "date-time",
                "include_in_schema": True,
            },
            "name": "from",
            "in": "header",
        },
        {
            "required": False,
            "schema": {
                "allOf": [{"$ref": "#/components/schemas/Range"}],
                "default": 20,
                "include_in_schema": True,
            },
            "name": "range",
            "in": "header",
        },
    ]


def test_invalid_schema_header():
    with pytest.raises(ImproperConfiguration) as ex:

        @get("/test")
        def invalid_path_parameter(cookie: NonPrimitiveSchema = Header()):
            pass

        build_route_handler(invalid_path_parameter)

    assert (
        str(ex.value)
        == "field: 'filter' with annotation:'<class 'tests.test_routing.sample.Filter'>' in "
        "'<class 'tests.test_routing.sample.NonPrimitiveSchema'>'can't be processed. "
        "Field type should belong to (<class 'list'>, <class 'set'>, <class 'tuple'>) "
        "or any primitive type"
    )
