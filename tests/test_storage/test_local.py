import os

import pytest
from ellar.common.datastructures import ContentFile
from ellar.core.files.storages import local
from ellar.core.files.storages.exceptions import UnsafeFileOperation
from ellar.core.files.storages.utils import validate_file_name


def _create_a_file(tmpdir):
    content_file = ContentFile(b"Local Storage test")
    fs = local.FileSystemStorage(location=tmpdir)

    fs.put("test.txt", content_file.file)
    return fs


def test_local_storage_put_function_works(tmpdir):
    fs = _create_a_file(tmpdir)
    assert ["test.txt"] == os.listdir(tmpdir)
    assert fs.service_name() == "local"

    with open(tmpdir / "test.txt", mode="rb") as fp:
        data = fp.readline()
    assert data == b"Local Storage test"


def test_local_storage_delete_function_works(tmpdir):
    fs = _create_a_file(tmpdir)
    assert ["test.txt"] == os.listdir(tmpdir)

    fs.delete("test.txt")
    assert [] == os.listdir(tmpdir)


def test_local_storage_file_url_works(tmpdir):
    fs = _create_a_file(tmpdir)
    assert ["test.txt"] == os.listdir(tmpdir)

    assert fs.locate("test.txt") == tmpdir / "test.txt"


def test_local_storage_open_function_works(tmpdir):
    fs = _create_a_file(tmpdir)
    assert ["test.txt"] == os.listdir(tmpdir)

    with fs.open("test.txt") as fp:
        data = fp.readline()
    assert data == b"Local Storage test"


def test_file_storage_create_parent_folder(tmpdir):
    _create_a_file(tmpdir / "new_test")
    assert ["test.txt"] == os.listdir(tmpdir / "new_test")


@pytest.mark.parametrize(
    "file_name",
    [
        "/tmp/.",
        "/tmp/..",
        "/tmp/../path",
        # "/tmp/path",
        "some/folder/",
        "some/folder/.",
        "some/folder/..",
        "some/folder/???",
        "some/folder/$.$.$",
        "some/../test.txt",
        "../path",
        "???",
        "$.$.$",
        "..",
        ".",
        "",
    ],
)
def test_generate_filename_upload_to_overrides_dangerous_filename(file_name, tmpdir):
    fs = local.FileSystemStorage(location=tmpdir)

    with pytest.raises(UnsafeFileOperation):
        fs.generate_filename(file_name)


@pytest.mark.parametrize(
    "file_name",
    [
        "/tmp/.",
        "/tmp/..",
        "/tmp/../path",
        "/tmp/path",
        "some/folder/",
        "some/folder/.",
        "some/folder/..",
        "some/folder/???",
        "some/folder/$.$.$",
        "some/../test.txt",
        "../path",
        "..",
        ".",
        "",
    ],
)
def test_invalid_file_name_validation(file_name):
    with pytest.raises(UnsafeFileOperation):
        validate_file_name(file_name)
