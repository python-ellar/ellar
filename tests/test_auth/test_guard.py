from ellar.auth import AuthenticationRequired, SkipAuth
from ellar.common import Controller, get
from ellar.common.serializer import serialize_object
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

SampleControllerPathSchema = {
    "/testing-authentication-required-guard/": {
        "get": {
            "tags": ["sample"],
            "operationId": "get_samples__get",
            "responses": {
                "200": {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "title": "Response Model",
                                "type": "object",
                            }
                        }
                    },
                }
            },
        }
    },
    "/testing-authentication-required-guard/{sample_id}": {
        "get": {
            "tags": ["sample"],
            "operationId": "get_sample_item_by_id__sample_id__get",
            "parameters": [
                {
                    "required": True,
                    "schema": {
                        "title": "Sample Id",
                        "type": "integer",
                        "include_in_schema": True,
                    },
                    "name": "sample_id",
                    "in": "path",
                }
            ],
            "responses": {
                "200": {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {
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
                            "schema": {
                                "$ref": "#/components/schemas/HTTPValidationError"
                            }
                        }
                    },
                },
            },
            "security": [{"JWT": []}],
        }
    },
}


@Controller("/testing-authentication-required-guard")
@AuthenticationRequired("JWT")
class SampleController:
    @get("/{sample_id:int}")
    def get_sample_item_by_id(self, sample_id: int):
        return f"sample {sample_id}"

    @get()
    @SkipAuth()
    def get_samples(self):
        return ["Sample 1", "Sample 2"]


test_module = Test.create_test_module(controllers=[SampleController])


def test_get_samples_works_for_anonymous():
    client = test_module.get_test_client()
    res = client.get("/testing-authentication-required-guard/")
    assert res.status_code == 200
    assert res.json() == ["Sample 1", "Sample 2"]


def test_get_sample_item_by_id_requires_user_identity():
    client = test_module.get_test_client()
    res = client.get("/testing-authentication-required-guard/1")
    assert res.status_code == 401
    assert res.json() == {"detail": "Forbidden", "status_code": 401}


def test_sample_controller_has_the_right_openapi_docs():
    document = serialize_object(
        OpenAPIDocumentBuilder().build_document(test_module.create_application())
    )
    assert document["paths"] == SampleControllerPathSchema
