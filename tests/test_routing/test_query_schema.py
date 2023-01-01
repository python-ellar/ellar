import pytest

from ellar.common import Query, get
from ellar.core import TestClientFactory
from ellar.core.connection import Request
from ellar.core.exceptions import ImproperConfiguration
from ellar.core.routing import ModuleRouter
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object

from .sample import Data, Filter, NonPrimitiveSchema

mr = ModuleRouter("")


@mr.get("/test")
def query_params_schema(
    request: Request,
    filters: Filter = Query(..., alias="will_not_work_for_schema_with_many_field"),
):
    return filters.dict()


@mr.get("/test-mixed")
def query_params_mixed_schema(
    request: Request,
    query1: int,
    query2: int = 5,
    filters: Filter = Query(...),
    data: Data = Query(...),
):
    return dict(query1=query1, query2=query2, filters=filters.dict(), data=data.dict())


tm = TestClientFactory.create_test_module(routers=(mr,))


def test_request():
    client = tm.get_client()
    response = client.get("/test?from=1&to=2&range=20&foo=1&range2=50")
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02+00:00",
        "from_datetime": "1970-01-01T00:00:01+00:00",
        "range": 20,
    }

    response = client.get("/test?from=1&to=2&range=21")
    assert response.status_code == 422


def test_request_mixed():
    client = tm.get_client()
    response = client.get(
        "/test-mixed?from=1&to=2&range=20&foo=1&range2=50&query1=2&int=3&float=1.6"
    )
    assert response.json() == {
        "query1": 2,
        "query2": 5,
        "filters": {
            "to_datetime": "1970-01-01T00:00:02+00:00",
            "from_datetime": "1970-01-01T00:00:01+00:00",
            "range": 20,
        },
        "data": {"an_int": 3, "a_float": 1.6},
    }

    response = client.get(
        "/test-mixed?from=1&to=2&range=20&foo=1&range2=50&query1=2&query2=10"
    )
    assert response.json() == {
        "query1": 2,
        "query2": 10,
        "filters": {
            "to_datetime": "1970-01-01T00:00:02+00:00",
            "from_datetime": "1970-01-01T00:00:01+00:00",
            "range": 20,
        },
        "data": {"an_int": 0, "a_float": 1.5},
    }

    response = client.get("/test-mixed?from=1&to=2")
    assert response.status_code == 422


def test_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(tm.app))
    params = document["paths"]["/test"]["get"]["parameters"]
    assert params == [
        {
            "required": False,
            "schema": {"title": "To", "type": "string", "format": "date-time"},
            "name": "to",
            "in": "query",
        },
        {
            "required": False,
            "schema": {"title": "From", "type": "string", "format": "date-time"},
            "name": "from",
            "in": "query",
        },
        {
            "required": False,
            "schema": {
                "allOf": [{"$ref": "#/components/schemas/Range"}],
                "default": 20,
            },
            "name": "range",
            "in": "query",
        },
    ]


def test_invalid_schema_query():
    with pytest.raises(ImproperConfiguration) as ex:

        @get("/test")
        def invalid_path_parameter(cookie: NonPrimitiveSchema = Query()):
            pass

    assert (
        str(ex.value)
        == "field: 'filter' with annotation:'<class 'tests.test_routing.sample.Filter'>' in "
        "'<class 'tests.test_routing.sample.NonPrimitiveSchema'>'can't be processed. "
        "Field type should belong to (<class 'list'>, <class 'set'>, <class 'tuple'>) "
        "or any primitive type"
    )
