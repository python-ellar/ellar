import asyncio
from pathlib import Path

import pytest
from ellar.common import Controller, ModuleRouter, file, get, serialize_object
from ellar.common.responses.models import (
    StreamingResponseModel,
    StreamingResponseModelInvalidContent,
)
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.testing import Test

BASEDIR = Path(__file__).resolve().parent.parent
FILE_RESPONSE_SCHEMA = {
    "200": {
        "description": "Successful Response",
        "content": {"text/html": {"schema": {"type": "string"}}},
    }
}


async def slow_numbers(minimum: int, maximum: int):
    yield ("<html><body><ul>")
    for number in range(minimum, maximum + 1):
        yield "<li>%d</li>" % number
        await asyncio.sleep(0.01)
    yield ("</ul></body></html>")


streaming_mr = ModuleRouter("/mr")


@streaming_mr.get(
    "/index-manual", response=StreamingResponseModel(media_type="text/html")
)
def file_template():
    return slow_numbers(1, 4)


@streaming_mr.get("/index-decorator")
@file(media_type="text/html", streaming=True)
def render_template():
    return slow_numbers(1, 4)


@Controller
class EllarController:
    @get(
        "/index-manual",
        response={200: StreamingResponseModel(media_type="text/html")},
    )
    def index2(self):
        """Looks for ellar/index since use_mvc=True"""
        return slow_numbers(1, 4)

    @get("/index-decorator")
    @file(media_type="text/html", streaming=True)
    def index(self):
        """detest its mvc and Looks for ellar/index"""
        return slow_numbers(1, 4)

    @get("/index-invalid")
    @file(media_type="text/html", streaming=True)
    def index3(self):
        """detest its mvc and Looks for ellar/index"""
        return {
            "path": f"{BASEDIR}/private/test.css",
            "filename": "file-test-css.css",
            "content_disposition_type": "whatever",
        }


test_module = Test.create_test_module(
    controllers=(EllarController,),
    routers=(streaming_mr,),
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
def test_file_stream_response_for_module_router_and_controller(path):
    client = test_module.get_test_client()
    response = client.get(path)
    response.raise_for_status()
    assert response.status_code == 200
    assert (
        response.text
        == "<html><body><ul><li>1</li><li>2</li><li>3</li><li>4</li></ul></body></html>"
    )


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
    with pytest.raises(
        StreamingResponseModelInvalidContent,
        match="Content must typing.AsyncIterable OR typing.Iterable",
    ):
        client.get("/ellar/index-invalid")
