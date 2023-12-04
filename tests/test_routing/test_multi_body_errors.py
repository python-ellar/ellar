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
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/items/": {
            "post": {
                "operationId": "save_item_no_body_items__post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "items": {"$ref": "#/components/schemas/Item2"},
                                "type": "array",
                                "title": "Item",
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
                                "schema": {"type": "object", "title": "Response Model"}
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
                "properties": {
                    "detail": {
                        "items": {"$ref": "#/components/schemas/ValidationError"},
                        "type": "array",
                        "title": "Details",
                    }
                },
                "type": "object",
                "required": ["detail"],
                "title": "HTTPValidationError",
            },
            "Item2": {
                "properties": {
                    "name": {"type": "string", "title": "Name"},
                    "age": {
                        "anyOf": [
                            {"type": "number", "exclusiveMinimum": 0.0},
                            {"type": "string"},
                        ],
                        "title": "Age",
                    },
                },
                "type": "object",
                "required": ["name", "age"],
                "title": "Item2",
            },
            "ValidationError": {
                "properties": {
                    "loc": {
                        "items": {"type": "string"},
                        "type": "array",
                        "title": "Location",
                    },
                    "msg": {"type": "string", "title": "Message"},
                    "type": {"type": "string", "title": "Error Type"},
                },
                "type": "object",
                "required": ["loc", "msg", "type"],
                "title": "ValidationError",
            },
        }
    },
    "tags": [],
}

single_error = {
    "detail": [
        {
            "ctx": {"gt": 0},
            "input": -1.0,
            "loc": ["body", 0, "age"],
            "msg": "Input should be greater than 0",
            "type": "greater_than",
            "url": "https://errors.pydantic.dev/2.5/v/greater_than",
        }
    ]
}

multiple_errors = {
    "detail": [
        {
            "type": "missing",
            "loc": ["body", 0, "name"],
            "msg": "Field required",
            "input": {"age": "five"},
            "url": "https://errors.pydantic.dev/2.5/v/missing",
        },
        {
            "type": "decimal_parsing",
            "loc": ["body", 0, "age"],
            "msg": "Input should be a valid decimal",
            "input": "five",
            "url": "https://errors.pydantic.dev/2.5/v/decimal_parsing",
        },
        {
            "type": "missing",
            "loc": ["body", 1, "name"],
            "msg": "Field required",
            "input": {"age": "six"},
            "url": "https://errors.pydantic.dev/2.5/v/missing",
        },
        {
            "type": "decimal_parsing",
            "loc": ["body", 1, "age"],
            "msg": "Input should be a valid decimal",
            "input": "six",
            "url": "https://errors.pydantic.dev/2.5/v/decimal_parsing",
        },
    ]
}


def test_openapi_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == openapi_schema


def test_put_correct_body():
    response = client.post("/items/", json=[{"name": "Foo", "age": 5}])
    assert response.status_code == 200, response.text
    assert response.json() == {"item": [{"name": "Foo", "age": "5"}]}


def test_jsonable_encoder_requiring_error():
    response = client.post("/items/", json=[{"name": "Foo", "age": -1.0}])
    assert response.status_code == 422, response.text
    json_result = response.json()
    assert json_result == single_error


def test_put_incorrect_body_multiple():
    response = client.post("/items/", json=[{"age": "five"}, {"age": "six"}])
    assert response.status_code == 422, response.text
    json_result = response.json()
    assert json_result == multiple_errors
