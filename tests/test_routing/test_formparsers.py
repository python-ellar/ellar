import os
import sys
from typing import List, Union

import pytest
from starlette.formparsers import UploadFile as StarletteUploadFile

from ellar.common import File, Form
from ellar.core import TestClientFactory
from ellar.core.datastructures import UploadFile
from ellar.core.routing import ModuleRouter

router = ModuleRouter("")


class ForceMultipartDict(dict):
    def __bool__(self):
        return True


# FORCE_MULTIPART is an empty dict that boolean-evaluates as `True`.
FORCE_MULTIPART = ForceMultipartDict()


@router.post
async def form_upload_single(test: UploadFile = File()):
    content = await test.read()
    return dict(
        test={
            "filename": test.filename,
            "content": content.decode(),
            "content_type": test.content_type,
        }
    )


@router.post("/mixed")
async def form_upload_single(test1: UploadFile = File(), test2: UploadFile = File()):
    content1 = await test1.read()
    content2 = await test2.read()

    return dict(
        test1={
            "filename": test1.filename,
            "content": content1.decode(),
            "content_type": test1.content_type,
        },
        test2={
            "filename": test2.filename,
            "content": content2.decode(),
            "content_type": test2.content_type,
        },
    )


@router.post("/multiple")
async def form_upload_multiple(test1: List[Union[UploadFile, str]] = File()):
    results = []
    for item in test1:
        if not isinstance(item, StarletteUploadFile):
            results.append(item)
            continue

        content = await item.read()
        results.append(
            {
                "filename": item.filename,
                "content": content.decode(),
                "content_type": item.content_type,
            }
        )
    return dict(test1=results)


@router.post("/mixed-optional")
async def form_upload_multiple(
    file: UploadFile = File(None),
    field: str = Form("", alias="field0"),
    field_2: str = Form(None, alias="field1"),
):
    _file = None
    if file:
        content = await file.read()
        _file = {
            "filename": file.filename,
            "content": content.decode(),
            "content_type": file.content_type,
        }
    return dict(
        file=_file,
        field0=field,
        field1=field_2,
    )


tm = TestClientFactory.create_test_module(routers=(router,))


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python >= 3.7")
def test_multipart_request_files(tmpdir):
    path = os.path.join(tmpdir, "test.txt")
    with open(path, "wb") as file:
        file.write(b"<file content>")

    client = tm.get_client()
    with open(path, "rb") as f:
        response = client.post("/", files={"test": f})
        assert response.json() == {
            "test": {
                "filename": "test.txt",
                "content": "<file content>",
                "content_type": "text/plain",
            }
        }


def test_multipart_request_files_with_content_type(tmpdir):
    path = os.path.join(tmpdir, "test.txt")
    with open(path, "wb") as file:
        file.write(b"<file content>")

    client = tm.get_client()
    with open(path, "rb") as f:
        response = client.post("/", files={"test": ("test.txt", f, "text/plain")})
        assert response.json() == {
            "test": {
                "filename": "test.txt",
                "content": "<file content>",
                "content_type": "text/plain",
            }
        }


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python >= 3.7")
def test_multipart_request_multiple_files(tmpdir):
    path1 = os.path.join(tmpdir, "test1.txt")
    with open(path1, "wb") as file:
        file.write(b"<file1 content>")

    path2 = os.path.join(tmpdir, "test2.txt")
    with open(path2, "wb") as file:
        file.write(b"<file2 content>")

    client = tm.get_client()
    with open(path1, "rb") as f1, open(path2, "rb") as f2:
        response = client.post(
            "/mixed", files={"test1": f1, "test2": ("test2.txt", f2, "text/plain")}
        )
        assert response.json() == {
            "test1": {
                "filename": "test1.txt",
                "content": "<file1 content>",
                "content_type": "text/plain",
            },
            "test2": {
                "filename": "test2.txt",
                "content": "<file2 content>",
                "content_type": "text/plain",
            },
        }


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python >= 3.7")
def test_multi_items(tmpdir):
    path1 = os.path.join(tmpdir, "test1.txt")
    with open(path1, "wb") as file:
        file.write(b"<file1 content>")

    path2 = os.path.join(tmpdir, "test2.txt")
    with open(path2, "wb") as file:
        file.write(b"<file2 content>")

    client = tm.get_client()
    with open(path1, "rb") as f1, open(path2, "rb") as f2:
        response = client.post(
            "/multiple",
            data={"test1": "abc"},
            files=[("test1", f1), ("test1", ("test2.txt", f2, "text/plain"))],
        )
        assert response.json() == {
            "test1": [
                "abc",
                {
                    "filename": "test1.txt",
                    "content": "<file1 content>",
                    "content_type": "text/plain",
                },
                {
                    "filename": "test2.txt",
                    "content": "<file2 content>",
                    "content_type": "text/plain",
                },
            ]
        }


def test_multipart_request_mixed_files_and_data(tmpdir):
    client = tm.get_client()
    response = client.post(
        "/mixed-optional",
        data=(
            # data
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="field0"\r\n\r\n'
            b"value0\r\n"
            # file
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="file"; filename="file.txt"\r\n'
            b"Content-Type: text/plain\r\n\r\n"
            b"<file content>\r\n"
            # data
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="field1"\r\n\r\n'
            b"value1\r\n"
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"
            )
        },
    )
    assert response.json() == {
        "file": {
            "filename": "file.txt",
            "content": "<file content>",
            "content_type": "text/plain",
        },
        "field0": "value0",
        "field1": "value1",
    }


def test_multipart_request_with_charset_for_filename(tmpdir):
    client = tm.get_client()
    response = client.post(
        "/mixed-optional",
        data=(
            # file
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="file"; filename="\xe6\x96\x87\xe6\x9b\xb8.txt"\r\n'
            b"Content-Type: text/plain\r\n\r\n"
            b"<file content>\r\n"
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; charset=utf-8; "
                "boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"
            )
        },
    )
    assert response.json() == {
        "file": {
            "filename": "文書.txt",
            "content": "<file content>",
            "content_type": "text/plain",
        },
        "field0": "",
        "field1": None,
    }


def test_multipart_request_without_charset_for_filename(tmpdir):
    client = tm.get_client()
    response = client.post(
        "/mixed-optional",
        data=(
            # file
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c\r\n"
            b'Content-Disposition: form-data; name="file"; filename="\xe7\x94\xbb\xe5\x83\x8f.jpg"\r\n'
            b"Content-Type: image/jpeg\r\n\r\n"
            b"<file content>\r\n"
            b"--a7f7ac8d4e2e437c877bb7b8d7cc549c--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; boundary=a7f7ac8d4e2e437c877bb7b8d7cc549c"
            )
        },
    )
    assert response.json() == {
        "file": {
            "filename": "画像.jpg",
            "content": "<file content>",
            "content_type": "image/jpeg",
        },
        "field0": "",
        "field1": None,
    }


def test_multipart_request_with_encoded_value(tmpdir):
    client = tm.get_client()
    response = client.post(
        "/multiple",
        data=(
            b"--20b303e711c4ab8c443184ac833ab00f\r\n"
            b"Content-Disposition: form-data; "
            b'name="test1"\r\n\r\n'
            b"Transf\xc3\xa9rer\r\n"
            b"--20b303e711c4ab8c443184ac833ab00f--\r\n"
        ),
        headers={
            "Content-Type": (
                "multipart/form-data; charset=utf-8; "
                "boundary=20b303e711c4ab8c443184ac833ab00f"
            )
        },
    )
    assert response.json() == {"test1": ["Transférer"]}


def test_urlencoded_request_data(tmpdir):
    client = tm.get_client()
    response = client.post("/multiple", data={"test1": "data"})
    assert response.json() == {"test1": ["data"]}


def test_no_request_data(tmpdir):
    client = tm.get_client()
    response = client.post("/mixed-optional")
    assert response.json() == {"file": None, "field0": "", "field1": None}


def test_urlencoded_percent_encoding(tmpdir):
    client = tm.get_client()
    response = client.post("/multiple", data={"test1": "da ta"})
    assert response.json() == {"test1": ["da ta"]}


def test_multipart_multi_field_app_reads_body(tmpdir):
    client = tm.get_client()
    response = client.post(
        "/multiple", data={"test1": "key pair"}, files=FORCE_MULTIPART
    )
    assert response.json() == {"test1": ["key pair"]}
