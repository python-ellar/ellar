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
    "openapi": "3.0.2",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/foo": {
            "post": {
                "operationId": "foo_foo_post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "title": "Items",
                                "allOf": [{"$ref": "#/components/schemas/Items_"}],
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
            "Items_": {
                "title": "Items_",
                "required": ["items"],
                "type": "object",
                "properties": {
                    "items": {
                        "title": "Items",
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
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


def test_body_extra_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == item_openapi_schema


def test_additional_properties_post():
    response = client.post("/foo", json={"items": {"foo": 1, "bar": 2}})
    assert response.status_code == 200, response.text
    assert response.json() == {"foo": 1, "bar": 2}
