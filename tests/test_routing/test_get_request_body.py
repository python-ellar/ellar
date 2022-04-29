from pydantic import BaseModel

from ellar.core.factory import ArchitekAppFactory
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object

app = ArchitekAppFactory.create_app()


class Product(BaseModel):
    name: str
    description: str = None  # type: ignore
    price: float


@app.Get("/product")
async def create_item(product: Product):
    return product


openapi_schema = {
    "openapi": "3.0.2",
    "info": {"title": "Architek Docs", "version": "1.0.0"},
    "paths": {
        "get": {
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Product"}
                    }
                },
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
            "operationId": "create_item_product_get",
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
    response = client.get("/product", json=body)
    assert response.json() == body
