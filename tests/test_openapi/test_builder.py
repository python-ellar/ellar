from ellar.common import Controller, get, put
from ellar.core import AppFactory
from ellar.openapi.builder import OpenAPIDocumentBuilder
from ellar.serializer import serialize_object


@Controller
class CatController:
    @get("/create")
    async def create_cat(self):
        return dict(message="created")

    @put("/{cat_id:int}")
    async def update_cat(self, cat_id: int):
        return dict(message="created", cat_id=cat_id)


def convert_server(url, description=None, **variables):
    return dict(url=url, description=description, variables=variables)


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
    details = dict(
        name="Eadwin", url="https://github.com/eadwinCode", email="eadwin@gmail.com"
    )
    builder = OpenAPIDocumentBuilder().set_contact(**details)
    assert builder._build["info"]["contact"] == details


def test_builder_set_license_works():
    details = dict(name="Yahoo", url="https://yahoo.com")
    builder = OpenAPIDocumentBuilder().set_license(**details)
    assert builder._build["info"]["license"] == details


def test_builder_set_external_doc_works():
    details = dict(
        description="More detailed documentation can be foound here",
        url="https://external-doc.com",
    )
    builder = OpenAPIDocumentBuilder().set_external_doc(**details)
    assert builder._build["externalDocs"] == details


def test_builder_add_server_works():
    server1 = dict(
        url="{server}/v1",
        description="Servers",
        server=dict(default="https://staging.server.com"),
    )
    server2 = dict(
        url="https://{environment}.example.com/v2",
        environment=dict(default="api", enum=["api", "api.dev", "api.staging"]),
    )
    builder = OpenAPIDocumentBuilder().add_server(**server1).add_server(**server2)
    servers = builder._build["servers"]
    assert len(servers) == 2
    assert servers[0] == convert_server(**server1)
    assert servers[1] == convert_server(**server2)


def test_builder_add_tags_works():
    tag1 = dict(name="tag1", description="some tag1 description")
    tag2 = dict(
        name="tag2",
        description="some tag2 description",
        external_doc_url="https://tag2.com",
        external_doc_description="some tag2 link description",
    )
    builder = OpenAPIDocumentBuilder().add_tags(**tag1).add_tags(**tag2)

    tags = builder._build["tags"]
    tag2_result = dict(
        name="tag2",
        description="some tag2 description",
        externalDocs=dict(
            url="https://tag2.com", description="some tag2 link description"
        ),
    )

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
                            "schema_": {"title": "Cat Id", "type": "integer"},
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
