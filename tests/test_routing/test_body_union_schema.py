from typing import Union
from unittest.mock import patch

from ellar.common import Body, post
from ellar.common.serializer import serialize_object
from ellar.core import Request
from ellar.openapi import OpenAPIDocumentBuilder, openapi_info
from ellar.testing import Test

from .sample import Item, OtherItem, Product

tm = Test.create_test_module()


@post("/items/")
def save_union_body_and_embedded_body(
    item: Union[OtherItem, Item], qty: Body[int, Body.P(default=12)]
):
    return {"item": item, "qty": qty}


@post("/items/embed")
def embed_qty(qty: Body[int, Body.P(12, embed=True)]):
    return {"qty": qty}


@post("/items/alias")
@openapi_info(tags=["Product"], description="Modify Product Qty", deprecated=True)
def alias_qty(
    qty: Body[
        int,
        Body.P(
            embed=True, alias="aliasQty", description="Product Qty", deprecated=True
        ),
    ],
):
    return {"qty": qty}


app = tm.create_application()
app.router.append(save_union_body_and_embedded_body)
app.router.append(embed_qty)
app.router.append(alias_qty)

client = tm.get_test_client()


item_openapi_schema = {
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/items/": {
            "post": {
                "operationId": "save_union_body_and_embedded_body_items__post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/body_save_union_body_and_embedded_body_items__post"
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
        },
        "/items/alias": {
            "post": {
                "tags": ["Product"],
                "description": "Modify Product Qty",
                "operationId": "alias_qty_items_alias_post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/body_alias_qty_items_alias_post"
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
                "deprecated": True,
            }
        },
        "/items/embed": {
            "post": {
                "operationId": "embed_qty_items_embed_post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "allOf": [
                                    {
                                        "$ref": "#/components/schemas/body_embed_qty_items_embed_post"
                                    }
                                ],
                                "title": "Body",
                            }
                        }
                    }
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
        },
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
            "Item": {
                "properties": {
                    "name": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "title": "Name",
                    }
                },
                "type": "object",
                "title": "Item",
            },
            "OtherItem": {
                "properties": {"price": {"type": "integer", "title": "Price"}},
                "type": "object",
                "required": ["price"],
                "title": "OtherItem",
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
            "body_alias_qty_items_alias_post": {
                "properties": {
                    "aliasQty": {
                        "type": "integer",
                        "title": "Aliasqty",
                        "description": "Product Qty",
                    }
                },
                "type": "object",
                "required": ["aliasQty"],
                "title": "body_alias_qty_items_alias_post",
            },
            "body_embed_qty_items_embed_post": {
                "properties": {
                    "qty": {"type": "integer", "title": "Qty", "default": 12}
                },
                "type": "object",
                "title": "body_embed_qty_items_embed_post",
            },
            "body_save_union_body_and_embedded_body_items__post": {
                "properties": {
                    "item": {
                        "anyOf": [
                            {"$ref": "#/components/schemas/OtherItem"},
                            {"$ref": "#/components/schemas/Item"},
                        ],
                        "title": "Item",
                    },
                    "qty": {"type": "integer", "title": "Qty", "default": 12},
                },
                "type": "object",
                "required": ["item"],
                "title": "body_save_union_body_and_embedded_body_items__post",
            },
        }
    },
    "tags": [],
}


def test_item_openapi_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == item_openapi_schema


def test_post_other_item():
    response = client.post("/items/", json={"item": {"price": 100}})
    assert response.status_code == 200, response.text
    assert response.json() == {"item": {"price": 100}, "qty": 12}


def test_post_item():
    response = client.post("/items/", json={"item": {"name": "Foo"}})
    assert response.status_code == 200, response.text
    assert response.json() == {"item": {"name": "Foo"}, "qty": 12}


def test_embed_body():
    response = client.post("/items/embed", json={"qty": 232})
    assert response.status_code == 200, response.text
    assert response.json() == {"qty": 232}


def test_embed_and_alias_body():
    response = client.post("/items/alias", json={"aliasQty": 232})
    assert response.status_code == 200, response.text
    assert response.json() == {"qty": 232}


def test_alias_with_more_body():
    @post("/product")
    async def create_item(
        product: "Product" = Body(alias="item"), qty: int = Body(alias="aliasQty")
    ):  # just to test get_typed_annotation in ellar.common.params.args.base
        return {"item": product, "aliasQty": qty}

    _tm = Test.create_test_module()
    _app = _tm.create_application()
    _app.router.append(create_item)

    _client = _tm.get_test_client()

    body = {
        "item": {"name": "Foo", "description": "Some description", "price": 5.5},
        "aliasQty": 234,
    }
    response = _client.post("/product", json=body)
    assert response.json() == body


@patch.object(Request, "body")
def test_body_resolution_fails(mock_form):
    async def raise_exception():
        raise Exception()

    mock_form.return_value = raise_exception
    response = client.post("/items/", json={"item": {"price": 100}})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "There was an error parsing the body",
        "status_code": 400,
    }
