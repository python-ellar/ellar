import pytest
from ellar.common import Cookie, Inject, ModuleRouter, get, serialize_object
from ellar.common.exceptions import ImproperConfiguration
from ellar.core.connection import Request
from ellar.core.routing.helper import build_route_handler
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

from .sample import Data, Filter, ListOfPrimitiveSchema, NonPrimitiveSchema

router = ModuleRouter("")


@router.get("/test/cookie")
def cookie_params_schema(
    request: Inject[Request],
    filters: Filter = Cookie(..., alias="will_not_work_for_schema_with_many_field"),
):
    return filters.dict()


@router.get("/test-mixed/cookie")
def cookie_params_mixed_schema(
    request: Inject[Request],
    filters: Cookie[Filter],
    data: Cookie[Data],
):
    return {"filters": filters.dict(), "data": data.dict()}


@router.post("/cookie-alias")
def cookie_with_alias(
    request: Inject[Request],
    qty: Cookie[str, Cookie.P(alias="aliasQty")],
):
    return {"aliasQty": qty}


tm = Test.create_test_module(routers=(router,))
app = tm.create_application()


def test_cookie_with_alias():
    client = tm.get_test_client()
    response = client.post(
        "/cookie-alias",
        json={},
        cookies={
            "aliasQty": "234",
        },
    )

    assert response.json() == {
        "aliasQty": "234",
    }

    response = client.post(
        "/cookie-alias",
        cookies={
            "qty": "234",
        },
    )
    assert response.status_code == 422
    json = response.json()
    assert json == {
        "detail": [
            {
                "loc": ["cookie", "aliasQty"],
                "msg": "none is not an allowed value",
                "type": "type_error.none.not_allowed",
            }
        ]
    }


def test_cookie_request():
    client = tm.get_test_client()
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
    client = tm.get_test_client()
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
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    params = document["paths"]["/test/cookie"]["get"]["parameters"]
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
            "in": "cookie",
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
            "in": "cookie",
        },
        {
            "required": False,
            "schema": {
                "allOf": [{"$ref": "#/components/schemas/Range"}],
                "default": 20,
                "include_in_schema": True,
            },
            "name": "range",
            "in": "cookie",
        },
    ]


def test_invalid_schema_cookie():
    with pytest.raises(ImproperConfiguration) as ex:

        @get("/test")
        def invalid_path_parameter(cookie: NonPrimitiveSchema = Cookie()):
            pass

        build_route_handler(invalid_path_parameter)

    assert (
        str(ex.value)
        == "field: 'filter' with annotation:'<class 'tests.test_routing.sample.Filter'>' in "
        "'<class 'tests.test_routing.sample.NonPrimitiveSchema'>'can't be processed. "
        "Field type is not a primitive type"
    )

    with pytest.raises(ImproperConfiguration) as ex:

        @get("/test")
        def invalid_path_parameter(cookie: ListOfPrimitiveSchema = Cookie()):
            pass

        build_route_handler(invalid_path_parameter)

    assert (
        str(ex.value) == "field: 'an_int' with annotation:'typing.List[int]' in "
        "'<class 'tests.test_routing.sample.ListOfPrimitiveSchema'>'can't be processed. "
        "Field type is not a primitive type"
    )
