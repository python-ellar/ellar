from typing import Dict

from ellar.common import post
from ellar.common.serializer import serialize_object
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test
from pydantic import BaseModel

tm = Test.create_test_module()


class Items_(BaseModel):
    items: Dict[str, int]


@post("/foo")
def foo(items: Items_):
    return items.items


app = tm.create_application()
app.router.append(foo)
client = tm.get_test_client()


item_openapi_schema = {
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/foo": {
            "post": {
                "operationId": "foo_foo_post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Items_"}
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
            "Items_": {
                "properties": {
                    "items": {
                        "additionalProperties": {"type": "integer"},
                        "type": "object",
                        "title": "Items",
                    }
                },
                "type": "object",
                "required": ["items"],
                "title": "Items_",
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


def test_body_extra_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == item_openapi_schema


def test_additional_properties_post():
    response = client.post("/foo", json={"items": {"foo": 1, "bar": 2}})
    assert response.status_code == 200, response.text
    assert response.json() == {"foo": 1, "bar": 2}
