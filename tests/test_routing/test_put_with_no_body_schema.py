from ellar.common import put, serialize_object
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

tm = Test.create_test_module()
app = tm.create_application()


@put("/items/{item_id}")
def save_item_no_body(item_id: str):
    return {"item_id": item_id}


app.router.append(save_item_no_body)
client = tm.get_test_client()


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/items/{item_id}": {
            "put": {
                "operationId": "save_item_no_body_items__item_id__put",
                "parameters": [
                    {
                        "required": True,
                        "schema": {
                            "title": "Item Id",
                            "type": "string",
                            "include_in_schema": True,
                        },
                        "name": "item_id",
                        "in": "path",
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


def test_openapi_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == openapi_schema


def test_put_no_body():
    response = client.put("/items/foo")
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}


def test_put_no_body_with_body():
    response = client.put("/items/foo", json={"name": "Foo"})
    assert response.status_code == 200, response.text
    assert response.json() == {"item_id": "foo"}
