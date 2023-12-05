from unittest.mock import patch

from ellar.common import post
from ellar.common.serializer import serialize_object
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

from ..utils import pydantic_error_url
from .sample import Product

tm = Test.create_test_module()


@post("/product")
async def create_item(
    product: "Product",
):  # just to test get_typed_annotation in ellar.common.params.args.base
    return product


tm.create_application().router.append(create_item)

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
    document = serialize_object(
        OpenAPIDocumentBuilder().build_document(tm.create_application())
    )
    assert document == openapi_schema


def test_get_with_body(test_client_factory):
    client = test_client_factory(tm.create_application())
    body = {"name": "Foo", "description": "Some description", "price": 5.5}
    response = client.post("/product", json=body)
    assert response.json() == body


def test_body_fails_for_invalid_json_data(test_client_factory):
    client = test_client_factory(tm.create_application())
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


def test_post_broken_body():
    client = tm.get_test_client()
    response = client.post(
        "/product",
        headers={"content-type": "application/json"},
        content="{some broken json}",
    )
    assert response.status_code == 422, response.text
    assert response.json() == (
        {
            "detail": [
                {
                    "type": "json_invalid",
                    "loc": ["body", 1],
                    "msg": "JSON decode error",
                    "input": {},
                    "ctx": {
                        "error": "Expecting property name enclosed in double quotes"
                    },
                }
            ]
        }
    )


def test_post_form_for_json():
    client = tm.get_test_client()
    response = client.post(
        "/product",
        data={"name": "Foo", "description": "Some description", "price": 5.5},
    )
    assert response.status_code == 422, response.text
    assert response.json() == (
        {
            "detail": [
                {
                    "type": "model_attributes_type",
                    "loc": ["body"],
                    "msg": "Input should be a valid dictionary or object to extract fields from",
                    "input": "name=Foo&description=Some+description&price=5.5",
                    "url": pydantic_error_url("model_attributes_type"),
                }
            ]
        }
    )


def test_explicit_content_type():
    client = tm.get_test_client()
    response = client.post(
        "/product",
        content='{"name": "Foo", "description": "Some description", "price": 5.5}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, response.text


def test_geo_json():
    client = tm.get_test_client()
    response = client.post(
        "/product",
        content='{"name": "Foo", "description": "Some description", "price": 5.5}',
        headers={"Content-Type": "application/geo+json"},
    )
    assert response.status_code == 200, response.text


def test_no_content_type_is_json():
    client = tm.get_test_client()
    response = client.post(
        "/product",
        content='{"name": "Foo", "description": "Some description", "price": 5.5}',
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "description": "Some description",
        "name": "Foo",
        "price": 5.5,
    }


def test_wrong_headers():
    client = tm.get_test_client()
    data = '{"name": "Foo", "description": "Some description", "price": 5.5}'
    response = client.post(
        "/product", content=data, headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 422, response.text
    assert response.json() == (
        {
            "detail": [
                {
                    "type": "model_attributes_type",
                    "loc": ["body"],
                    "msg": "Input should be a valid dictionary or object to extract fields from",
                    "input": '{"name": "Foo", "description": "Some description", "price": 5.5}',
                    "url": pydantic_error_url(
                        "model_attributes_type"
                    ),  # "https://errors.pydantic.dev/0.38.0/v/dict_attributes_type",
                }
            ]
        }
    )

    response = client.post(
        "/product", content=data, headers={"Content-Type": "application/geo+json-seq"}
    )
    assert response.status_code == 422, response.text
    assert response.json() == (
        {
            "detail": [
                {
                    "type": "model_attributes_type",
                    "loc": ["body"],
                    "msg": "Input should be a valid dictionary or object to extract fields from",
                    "input": '{"name": "Foo", "description": "Some description", "price": 5.5}',
                    "url": pydantic_error_url("model_attributes_type"),
                }
            ]
        }
    )
    response = client.post(
        "/product",
        content=data,
        headers={"Content-Type": "application/not-really-json"},
    )
    assert response.status_code == 422, response.text
    assert response.json() == (
        {
            "detail": [
                {
                    "type": "model_attributes_type",
                    "loc": ["body"],
                    "msg": "Input should be a valid dictionary or object to extract fields from",
                    "input": '{"name": "Foo", "description": "Some description", "price": 5.5}',
                    "url": pydantic_error_url("model_attributes_type"),
                }
            ]
        }
    )


def test_other_exceptions():
    client = tm.get_test_client()
    with patch("json.loads", side_effect=Exception):
        response = client.post("/product", json={"test": "test2"})
        assert response.status_code == 400, response.text
