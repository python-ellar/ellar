from ellar.common import Controller, get, serialize_object
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test


@Controller
class Cat1Controller:
    @get("/create")
    async def create_cat(self):
        return {"message": "created"}


@Controller
class Cat2Controller:
    @get("/create")
    async def create_cat(self):
        return {"message": "created"}


Cat2Controller.add_router(Cat1Controller)


tm = Test.create_test_module(controllers=[Cat2Controller])


def test_nested_route_openapi_schema():
    app = tm.create_application()
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document == NESTED_SCHEMA


NESTED_SCHEMA = {
    "openapi": "3.1.0",
    "info": {"title": "Ellar API Docs", "version": "1.0.0"},
    "paths": {
        "/cat2/cat1/create": {
            "get": {
                "tags": ["cat2:cat1"],
                "operationId": "create_cat_create_get__cat1",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "title": "Response Model"}
                            }
                        },
                    }
                },
            }
        },
        "/cat2/create": {
            "get": {
                "tags": ["cat2"],
                "operationId": "create_cat_create_get__cat2",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object", "title": "Response Model"}
                            }
                        },
                    }
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
    "tags": [{"name": "cat2:cat1"}, {"name": "cat2"}],
}
