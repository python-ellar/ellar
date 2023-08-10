from ellar.common import Controller, ModuleRouter, get, serialize_object
from ellar.openapi import ApiTags, OpenAPIDocumentBuilder
from ellar.testing import Test
from pydantic import AnyUrl

another_router = ModuleRouter("/prefix/another", name="arouter")


@another_router.get("/index")
def index():
    return "ok"


@Controller(prefix="/items/{orgID:int}", name="override_name")
class MyController:
    @get("/index")
    def index(self):
        return "ok"


@Controller(prefix="/items/{orgID:int}")
@ApiTags(
    description="Some description",
    external_doc_description="external",
    name="dec",
    external_doc_url="https://example.com",
)
class MyControllerAPITags:
    @get("/index")
    def index(self):
        return "ok"


def test_openapi_tag_for_module():
    app = Test.create_test_module(routers=[another_router]).create_application()
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document["tags"] == [{"name": "arouter"}]


def test_openapi_tag_with_api_tags():
    ApiTags(name="Another Module Router", description="Another router description")(
        another_router.get_control_type()
    )
    app = Test.create_test_module(routers=[another_router]).create_application()

    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document["tags"] == [
        {"name": "Another Module Router", "description": "Another router description"}
    ]


def test_controller_openapi_build():
    app = Test.create_test_module(controllers=[MyController]).create_application()
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document["tags"] == [{"name": "override_name"}]


def test_controller_with_api_tags():
    app = Test.create_test_module(
        controllers=[MyControllerAPITags]
    ).create_application()
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    assert document["tags"] == [
        {
            "description": "Some description",
            "externalDocs": {
                "description": "external",
                "url": AnyUrl(
                    "https://example.com",
                    scheme="https",
                    host="example.com",
                    tld="com",
                    host_type="domain",
                ),
            },
            "name": "dec",
        }
    ]
