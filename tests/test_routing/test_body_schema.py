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
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/product": {
            "post": {
                "operationId": "create_item_product_post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Product"}
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
            "Product": {
                "properties": {
                    "name": {"type": "string", "title": "Name"},
                    "description": {"type": "string", "title": "Description"},
                    "price": {"type": "number", "title": "Price"},
                },
                "type": "object",
                "required": ["name", "price"],
                "title": "Product",
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
    response = client.post("/product", json=body)
    assert response.json() == {
        "detail": [
            {
                "type": "model_attributes_type",
                "loc": ["body"],
                "msg": "Input should be a valid dictionary or object to extract fields from",
                "input": '\n{\n    "name": "John",\n    "age": 30,\n    "is_student": True,\n    "favorite_colors": ["red", "blue", "green"],\n    "address": {\n        "street": "123 Main St",\n        "city": "Some City",\n        "zip": "12345"\n    },\n    "unterminated_quote": "This string is not properly terminated,\n}\n',
                "url": "https://errors.pydantic.dev/2.5/v/model_attributes_type",
            }
        ]
    }
