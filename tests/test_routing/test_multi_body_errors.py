from decimal import Decimal
from typing import List

from ellar.common import post, serialize_object
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test
from pydantic import BaseModel, condecimal

tm = Test.create_test_module()
app = tm.create_application()


class Item2(BaseModel):
    name: str
    age: condecimal(gt=Decimal(0.0))  # type: ignore


@post("/items/")
def save_item_no_body(item: List[Item2]):
    return {"item": item}


app.router.append(save_item_no_body)
client = tm.get_test_client()


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/items/": {
            "post": {
                "operationId": "save_item_no_body_items__post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "title": "Item",
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Item2"},
                                "include_in_schema": True,
                            }
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"title": "Response Model", "type": "object"}
                            }
                        },
                    },
                    "422": {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/HTTPValidationError"
                                }
                            }
                        },
                    },
                },
            }
        }
    },
    "components": {
        "schemas": {
            "HTTPValidationError": {
                "title": "HTTPValidationError",
                "required": ["detail"],
                "type": "object",
                "properties": {
                    "detail": {
                        "title": "Details",
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                    }
                },
            },
            "Item2": {
                "title": "Item2",
                "required": ["name", "age"],
                "type": "object",
                "properties": {
                    "name": {"title": "Name", "type": "string"},
                    "age": {"title": "Age", "exclusiveMinimum": 0.0, "type": "number"},
                },
            },
            "ValidationError": {
                "title": "ValidationError",
                "required": ["loc", "msg", "type"],
                "type": "object",
                "properties": {
                    "loc": {
                        "title": "Location",
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "msg": {"title": "Message", "type": "string"},
                    "type": {"title": "Error Type", "type": "string"},
                },
            },
        }
    },
    "tags": [],
}

single_error = {
    "detail": [
        {
            "ctx": {"limit_value": 0.0},
            "loc": ["body", 0, "age"],
            "msg": "ensure this value is greater than 0",
            "type": "value_error.number.not_gt",
        }
    ]
}

multiple_errors = {
    "detail": [
        {
            "loc": ["body", 0, "name"],
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ["body", 0, "age"],
            "msg": "value is not a valid decimal",
            "type": "type_error.decimal",
        },
        {
            "loc": ["body", 1, "name"],
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ["body", 1, "age"],
            "msg": "value is not a valid decimal",
            "type": "type_error.decimal",
        },
    ]
}


def test_openapi_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == openapi_schema


def test_put_correct_body():
    response = client.post("/items/", json=[{"name": "Foo", "age": 5}])
    assert response.status_code == 200, response.text
    assert response.json() == {"item": [{"name": "Foo", "age": 5}]}


def test_jsonable_encoder_requiring_error():
    response = client.post("/items/", json=[{"name": "Foo", "age": -1.0}])
    assert response.status_code == 422, response.text
    assert response.json() == single_error


def test_put_incorrect_body_multiple():
    response = client.post("/items/", json=[{"age": "five"}, {"age": "six"}])
    assert response.status_code == 422, response.text
    assert response.json() == multiple_errors
