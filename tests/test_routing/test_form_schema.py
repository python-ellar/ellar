import pytest
from ellar.common import Form, Inject, ModuleRouter, post, serialize_object
from ellar.common.exceptions import ImproperConfiguration
from ellar.core.connection import Request
from ellar.core.routing.helper import build_route_handler
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

from .sample import Filter, NonPrimitiveSchema

mr = ModuleRouter("")


@mr.post("/form-schema")
def form_params_schema(
    request: Inject[Request],
    filters: Filter = Form(..., alias="will_not_work_for_schema_with_many_field"),
):
    return filters.dict()


@mr.post("/form-alias")
def form_with_alias(
    request: Inject[Request],
    qty: int = Form(..., alias="aliasQty"),
):
    return {"aliasQty": qty}


test_module = Test.create_test_module(routers=(mr,))
app = test_module.create_application()


def test_request():
    client = test_module.get_test_client()
    response = client.post("/form-schema", data={"from": "1", "to": "2", "range": "20"})
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02+00:00",
        "from_datetime": "1970-01-01T00:00:01+00:00",
        "range": 20,
    }

    response = client.post(
        "/form-schema", data={"from": "1", "to": "2", "range": "100"}
    )
    assert response.status_code == 422
    json = response.json()
    assert json == {
        "detail": [
            {
                "loc": ["body", "range"],
                "msg": "value is not a valid enumeration member; permitted: 20, 50, 200",
                "type": "type_error.enum",
                "ctx": {"enum_values": [20, 50, 200]},
            }
        ]
    }


def test_form_with_alias():
    client = test_module.get_test_client()
    response = client.post(
        "/form-alias",
        data={
            "aliasQty": 234,
        },
    )
    assert response.json() == {
        "aliasQty": 234,
    }

    response = client.post(
        "/form-alias",
        data={
            "qty": 234,
        },
    )
    assert response.status_code == 422
    json = response.json()
    assert json == {
        "detail": [
            {
                "loc": ["body", "aliasQty"],
                "msg": "value is not a valid integer",
                "type": "type_error.integer",
            }
        ]
    }


def test_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    params = document["paths"]["/form-schema"]["post"]["requestBody"]
    assert params == {
        "content": {
            "application/form-data": {
                "schema": {
                    "allOf": [
                        {
                            "$ref": "#/components/schemas/body_form_params_schema_form_schema_post"
                        }
                    ],
                    "include_in_schema": True,
                    "title": "Body",
                }
            }
        }
    }
    schema = document["components"]["schemas"][
        "body_form_params_schema_form_schema_post"
    ]
    assert schema == {
        "title": "body_form_params_schema_form_schema_post",
        "type": "object",
        "properties": {
            "to": {
                "title": "To",
                "type": "string",
                "format": "date-time",
                "include_in_schema": True,
            },
            "from": {
                "title": "From",
                "type": "string",
                "format": "date-time",
                "include_in_schema": True,
            },
            "range": {
                "allOf": [{"$ref": "#/components/schemas/Range"}],
                "default": 20,
                "include_in_schema": True,
            },
        },
    }


def test_for_invalid_schema():
    with pytest.raises(ImproperConfiguration) as ex:

        @post("/test")
        def invalid_path_parameter(path: NonPrimitiveSchema = Form()):
            pass

        build_route_handler(invalid_path_parameter)

    assert (
        str(ex.value)
        == "field: 'filter' with annotation:'<class 'tests.test_routing.sample.Filter'>' in "
        "'<class 'tests.test_routing.sample.NonPrimitiveSchema'>'can't be processed. "
        "Field type should belong to (<class 'list'>, <class 'set'>, <class 'tuple'>) "
        "or any primitive type"
    )
