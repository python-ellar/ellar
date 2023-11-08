from ellar.app import AppFactory
from ellar.common import post
from ellar.common.serializer import serialize_object
from ellar.openapi import OpenAPIDocumentBuilder

from .sample import Product

app = AppFactory.create_app()


@post("/product")
async def create_item(
    product: "Product",
):  # just to test get_typed_annotation in ellar.common.params.args.base
    return product


app.router.append(create_item)

openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/product": {
            "post": {
                "operationId": "create_item_product_post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "title": "Product",
                                "allOf": [{"$ref": "#/components/schemas/Product"}],
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
            "Product": {
                "title": "Product",
                "required": ["name", "price"],
                "type": "object",
                "properties": {
                    "name": {"title": "Name", "type": "string"},
                    "description": {"title": "Description", "type": "string"},
                    "price": {"title": "Price", "type": "number"},
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


def test_get_with_body(test_client_factory):
    client = test_client_factory(app)
    body = {"name": "Foo", "description": "Some description", "price": 5.5}
    response = client.post("/product", json=body)
    assert response.json() == body


def test_body_fails_for_invalid_json_data(test_client_factory):
    client = test_client_factory(app)
    body = """
{
    "name": "John",
    "age": 30,
    "is_student": True,
    "favorite_colors": ["red", "blue", "green"],
    "address": {
        "street": "123 Main St",
        "city": "Some City",
        "zip": "12345"
    },
    "unterminated_quote": "This string is not properly terminated,
}
"""
    response = client.post("/product", data=body)
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", 56],
                "msg": "Expecting value: line 5 column 19 (char 56)",
                "type": "value_error.jsondecode",
                "ctx": {
                    "msg": "Expecting value",
                    "doc": '\n{\n    "name": "John",\n    "age": 30,\n    "is_student": True,\n    "favorite_colors": ["red", "blue", "green"],\n    "address": {\n        "street": "123 Main St",\n        "city": "Some City",\n        "zip": "12345"\n    },\n    "unterminated_quote": "This string is not properly terminated,\n}\n',
                    "pos": 56,
                    "lineno": 5,
                    "colno": 19,
                },
            }
        ]
    }
