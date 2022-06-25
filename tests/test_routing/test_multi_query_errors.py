from typing import List

from ellar.common import Query, get
from ellar.core import TestClientFactory
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object

tm = TestClientFactory.create_test_module()


@get("/items/")
def read_items(q: List[int] = Query(None)):
    return {"q": q}


tm.app.router.append(read_items)
client = tm.get_client()


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/items/": {
            "get": {
                "operationId": "read_items_items__get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {
                            "title": "Q",
                            "type": "array",
                            "items": {"type": "integer"},
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

multiple_errors = {
    "detail": [
        {
            "loc": ["query", "q", 0],
            "msg": "value is not a valid integer",
            "type": "type_error.integer",
        },
        {
            "loc": ["query", "q", 1],
            "msg": "value is not a valid integer",
            "type": "type_error.integer",
        },
    ]
}


def test_openapi_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(tm.app))
    assert document == openapi_schema


def test_multi_query():
    response = client.get("/items/?q=5&q=6")
    assert response.status_code == 200, response.text
    assert response.json() == {"q": [5, 6]}


def test_multi_query_incorrect():
    response = client.get("/items/?q=five&q=six")
    assert response.status_code == 422, response.text
    assert response.json() == multiple_errors
