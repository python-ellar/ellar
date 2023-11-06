from ellar.app import AppFactory
from ellar.common import Controller, get, put, serialize_object
from ellar.openapi.builder import OpenAPIDocumentBuilder
from ellar.openapi.openapi_v3 import APIKeyIn


@Controller
class CatController:
    @get("/create")
    async def create_cat(self):
        return {"message": "created"}

    @put("/{cat_id:int}")
    async def update_cat(self, cat_id: int):
        return {"message": "created", "cat_id": cat_id}


def convert_server(url, description=None, **variables):
    return {"url": url, "description": description, "variables": variables}


def test_builder_defaults():
    builder = OpenAPIDocumentBuilder()
    assert builder._build["info"]["title"] == "Ellar API Docs"
    assert builder._build["info"]["version"] == "1.0.0"
    assert builder._build["tags"] == []
    assert builder._build["openapi"] == "3.0.2"


def test_set_openapi_version_works():
    builder = OpenAPIDocumentBuilder()
    builder.set_openapi_version("2.0.0")
    assert builder._build["openapi"] == "2.0.0"


def test_builder_set_title_works():
    builder = OpenAPIDocumentBuilder()
    builder.set_title("Some new title")
    assert builder._build["info"]["title"] == "Some new title"


def test_builder_set_version_works():
    builder = OpenAPIDocumentBuilder()
    builder.set_version("2.0.0")
    assert builder._build["info"]["version"] == "2.0.0"


def test_builder_set_description_works():
    description = "Whatever description available"
    builder = OpenAPIDocumentBuilder()
    builder.set_description(description)
    assert builder._build["info"]["description"] == description


def test_builder_set_term_of_service_works():
    terms_of_service = "What terms of service available"
    builder = OpenAPIDocumentBuilder().set_term_of_service(terms_of_service)
    assert builder._build["info"]["termsOfService"] == terms_of_service


def test_builder_set_contact_works():
    details = {
        "name": "Eadwin",
        "url": "https://github.com/eadwinCode",
        "email": "eadwin@gmail.com",
    }
    builder = OpenAPIDocumentBuilder().set_contact(**details)
    assert builder._build["info"]["contact"] == details


def test_builder_set_license_works():
    details = {"name": "Yahoo", "url": "https://yahoo.com"}
    builder = OpenAPIDocumentBuilder().set_license(**details)
    assert builder._build["info"]["license"] == details


def test_builder_set_external_doc_works():
    details = {
        "description": "More detailed documentation can be foound here",
        "url": "https://external-doc.com",
    }
    builder = OpenAPIDocumentBuilder().set_external_doc(**details)
    assert builder._build["externalDocs"] == details


def test_add_security_requirements():
    builder = OpenAPIDocumentBuilder().add_security_requirements(
        name="a", requirements=["b", "c"]
    )
    assert builder._build["security"] == [{"a": ["b", "c"]}]


def test_add_api_key():
    builder = OpenAPIDocumentBuilder().add_api_key(
        openapi_in=APIKeyIn.cookie, openapi_description="Cookie description"
    )
    assert builder._build["components"]["securitySchemes"] == {
        "api_key": {
            "description": "Cookie description",
            "in": "cookie",
            "name": "api_key",
            "type": "apiKey",
        }
    }


def test_add_cookie_auth():
    builder = OpenAPIDocumentBuilder().add_cookie_auth(
        cookie_name="test-cookie", openapi_description="Cookie description"
    )
    assert builder._build["components"]["securitySchemes"] == {
        "cookie": {
            "description": "Cookie description",
            "in": "cookie",
            "name": "test-cookie",
            "type": "apiKey",
        }
    }


def test_add_basic_auth():
    builder = OpenAPIDocumentBuilder().add_basic_auth()
    assert builder._build["components"]["securitySchemes"] == {
        "basic": {
            "description": None,
            "name": "basic",
            "scheme": "basic",
            "type": "http",
        }
    }


def test_add_bearer_auth():
    builder = OpenAPIDocumentBuilder().add_bearer_auth()
    assert builder._build["components"]["securitySchemes"] == {
        "bearer": {
            "bearerFormat": "JWT",
            "description": None,
            "name": "bearer",
            "scheme": "bearer",
            "type": "http",
        }
    }


def test_builder_add_server_works():
    server1 = {
        "url": "{server}/v1",
        "description": "Servers",
        "server": {"default": "https://staging.server.com"},
    }
    server2 = {
        "url": "https://{environment}.example.com/v2",
        "environment": {"default": "api", "enum": ["api", "api.dev", "api.staging"]},
    }
    builder = OpenAPIDocumentBuilder().add_server(**server1).add_server(**server2)
    servers = builder._build["servers"]
    assert len(servers) == 2
    assert servers[0] == convert_server(**server1)
    assert servers[1] == convert_server(**server2)


def test_builder_add_tags_works():
    tag1 = {"name": "tag1", "description": "some tag1 description"}
    tag2 = {
        "name": "tag2",
        "description": "some tag2 description",
        "external_doc_url": "https://tag2.com",
        "external_doc_description": "some tag2 link description",
    }
    builder = OpenAPIDocumentBuilder().add_tags(**tag1).add_tags(**tag2)

    tags = builder._build["tags"]
    tag2_result = {
        "name": "tag2",
        "description": "some tag2 description",
        "externalDocs": {
            "url": "https://tag2.com",
            "description": "some tag2 link description",
        },
    }

    assert len(tags) == 2
    assert tags[0] == tag1
    assert tags[1] == tag2_result


def test_builder_build_document_adds_error_schemas():
    app = AppFactory.create_app()
    builder = OpenAPIDocumentBuilder()
    schema = builder.build_document(app)

    scheme_dict = serialize_object(schema.dict(exclude_none=True))
    assert "HTTPValidationError" in scheme_dict["components"]["schemas"]
    assert "ValidationError" in scheme_dict["components"]["schemas"]


def test_builder_build_document_has_correct_schema():
    app = AppFactory.create_app(controllers=(CatController,))
    builder = OpenAPIDocumentBuilder()
    schema = builder.build_document(app)

    scheme_dict = serialize_object(schema.dict(exclude_none=True))
    assert "HTTPValidationError" in scheme_dict["components"]["schemas"]
    assert "ValidationError" in scheme_dict["components"]["schemas"]

    assert scheme_dict == {
        "openapi": "3.0.2",
        "info": {"title": "Ellar API Docs", "version": "1.0.0"},
        "paths": {
            "/cat/create": {
                "get": {
                    "tags": ["cat"],
                    "operationId": "create_cat_create_get",
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema_": {
                                        "title": "Response Model",
                                        "type": "object",
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/cat/{cat_id}": {
                "put": {
                    "tags": ["cat"],
                    "operationId": "update_cat__cat_id__put",
                    "parameters": [
                        {
                            "required": True,
                            "schema_": {
                                "title": "Cat Id",
                                "type": "integer",
                                "include_in_schema": True,
                            },
                            "name": "cat_id",
                            "in_": "path",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema_": {
                                        "title": "Response Model",
                                        "type": "object",
                                    }
                                }
                            },
                        },
                        "422": {
                            "description": "Validation Error",
                            "content": {
                                "application/json": {
                                    "schema_": {
                                        "ref": "#/components/schemas/HTTPValidationError"
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
                    "title": "HTTPValidationError",
                    "required": ["detail"],
                    "type": "object",
                    "properties": {
                        "detail": {
                            "title": "Details",
                            "type": "array",
                            "items": {"ref": "#/components/schemas/ValidationError"},
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
        "tags": [{"name": "cat"}],
    }
