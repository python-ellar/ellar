from typing import List

from ellar.common import Query, get, serialize_object
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

tm = Test.create_test_module()
app = tm.create_application()


@get("/items/")
def read_items(q: List[int] = Query(None)):
    return {"q": q}


app.router.append(read_items)
client = tm.get_test_client()


openapi_schema = {
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/items/": {
            "get": {
                "operationId": "read_items_items__get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {
                            "items": {"type": "integer"},
                            "type": "array",
                            "title": "Q",
                        },
                        "name": "q",
                        "in": "query",
                    }
                ],
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

multiple_errors = {
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["query", "q", 0],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "input": "five",
            "url": "https://errors.pydantic.dev/2.5/v/int_parsing",
        },
        {
            "type": "int_parsing",
            "loc": ["query", "q", 1],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "input": "six",
            "url": "https://errors.pydantic.dev/2.5/v/int_parsing",
        },
    ]
}


def test_openapi_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == openapi_schema


def test_multi_query():
    response = client.get("/items/?q=5&q=6")
    assert response.status_code == 200, response.text
    assert response.json() == {"q": [5, 6]}


def test_multi_query_incorrect():
    response = client.get("/items/?q=five&q=six")
    assert response.status_code == 422, response.text
    json_result = response.json()
    assert json_result == multiple_errors
