from pathlib import Path

import pytest
from ellar.common import Controller, ModuleRouter, file, get, serialize_object
from ellar.common.responses.models import FileResponseModel
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

BASEDIR = Path(__file__).resolve().parent.parent
FILE_RESPONSE_SCHEMA = {
    "200": {
        "description": "Successful Response",
        "content": {"text/css": {"schema": {"type": "string"}}},
    }
}


mr = ModuleRouter("/mr")


@mr.get("/index-manual", response=FileResponseModel(media_type="text/css"))
def file_template():
    return {"path": f"{BASEDIR}/private/test.css", "filename": "file-test-css.css"}


@mr.get("/index-decorator")
@file(media_type="text/css")
def render_template():
    return {"path": f"{BASEDIR}/private/test.css", "filename": "file-test-css.css"}


@Controller
class EllarController:
    @get(
        "/index-manual",
        response={200: FileResponseModel(media_type="text/css")},
    )
    def index2(self):
        """Looks for ellar/index since use_mvc=True"""
        return {"path": f"{BASEDIR}/private/test.css", "filename": "file-test-css.css"}

    @get("/index-decorator")
    @file(media_type="text/css")
    def index(self):
        """detest its mvc and Looks for ellar/index"""
        return {"path": f"{BASEDIR}/private/test.css", "filename": "file-test-css.css"}

    @get("/index-invalid")
    @file(media_type="text/css")
    def index3(self):
        """detest its mvc and Looks for ellar/index"""
        return {
            "path": f"{BASEDIR}/private/test.css",
            "filename": "file-test-css.css",
            "content_disposition_type": "whatever",
        }


test_module = Test.create_test_module(
    controllers=(EllarController,),
    routers=(mr,),
)
app = test_module.create_application()
document = serialize_object(OpenAPIDocumentBuilder().build_document(app))


@pytest.mark.parametrize(
    "path",
    [
        "/ellar/index-manual",
        "/ellar/index-decorator",
        "/mr/index-manual",
        "/mr/index-decorator",
    ],
)
def test_file_response_for_module_router_and_controller(path):
    client = test_module.get_test_client()
    response = client.get(path)
    response.raise_for_status()
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="file-test-css.css"'
    )
    assert response.headers["content-length"] == "23"
    assert response.headers["etag"]
    assert response.text == ".div {background: red}\n"


@pytest.mark.parametrize(
    "path",
    [
        "/ellar/index-manual",
        "/ellar/index-decorator",
        "/mr/index-manual",
        "/mr/index-decorator",
    ],
)
def test_response_schema(path):
    path_response = document["paths"][path]["get"]["responses"]
    assert path_response == FILE_RESPONSE_SCHEMA


def test_invalid_parameter_returned():
    client = test_module.get_test_client()
    response = client.get("/ellar/index-invalid")
    assert response.status_code == 422

    assert response.json() == {
        "detail": [
            {
                "loc": ["response_model", "content_disposition_type"],
                "msg": "value is not a valid enumeration member; permitted: 'inline', 'attachment'",
                "type": "type_error.enum",
                "ctx": {"enum_values": ["inline", "attachment"]},
            }
        ]
    }
