import pytest
from ellar.common import File, Form, ModuleRouter, UploadFile
from ellar.common.params.args.request_model import (
    multipart_incorrect_install_error,
    multipart_not_installed_error,
)
from ellar.core.routing import get_controller_builder_factory

builder = get_controller_builder_factory(ModuleRouter)


def test_incorrect_multipart_installed_form(monkeypatch):
    monkeypatch.delattr("multipart.multipart.parse_options_header", raising=False)
    with pytest.raises(RuntimeError, match=multipart_incorrect_install_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(username: str = Form()):
            return username  # pragma: nocover

        builder.build(router)


def test_incorrect_multipart_installed_file_upload(monkeypatch):
    monkeypatch.delattr("multipart.multipart.parse_options_header", raising=False)
    with pytest.raises(RuntimeError, match=multipart_incorrect_install_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(f: UploadFile = File()):
            return f  # pragma: nocover

        builder.build(router)


def test_incorrect_multipart_installed_file_bytes(monkeypatch):
    monkeypatch.delattr("multipart.multipart.parse_options_header", raising=False)
    with pytest.raises(RuntimeError, match=multipart_incorrect_install_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(f: bytes = File()):
            return f  # pragma: nocover

        builder.build(router)


def test_incorrect_multipart_installed_multi_form(monkeypatch):
    monkeypatch.delattr("multipart.multipart.parse_options_header", raising=False)
    with pytest.raises(RuntimeError, match=multipart_incorrect_install_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(username: str = Form(), password: str = Form()):
            return username  # pragma: nocover

        builder.build(router)


def test_incorrect_multipart_installed_form_file(monkeypatch):
    monkeypatch.delattr("multipart.multipart.parse_options_header", raising=False)
    with pytest.raises(RuntimeError, match=multipart_incorrect_install_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(username: str = Form(), f: UploadFile = File()):
            return username  # pragma: nocover

        builder.build(router)


def test_no_multipart_installed(monkeypatch):
    monkeypatch.delattr("multipart.__version__", raising=False)
    with pytest.raises(RuntimeError, match=multipart_not_installed_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(username: str = Form()):
            return username  # pragma: nocover

        builder.build(router)


def test_no_multipart_installed_file(monkeypatch):
    monkeypatch.delattr("multipart.__version__", raising=False)
    with pytest.raises(RuntimeError, match=multipart_not_installed_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(f: UploadFile = File()):
            return f  # pragma: nocover

        builder.build(router)


def test_no_multipart_installed_file_bytes(monkeypatch):
    monkeypatch.delattr("multipart.__version__", raising=False)
    with pytest.raises(RuntimeError, match=multipart_not_installed_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(f: bytes = File()):
            return f  # pragma: nocover

        builder.build(router)


def test_no_multipart_installed_multi_form(monkeypatch):
    monkeypatch.delattr("multipart.__version__", raising=False)
    with pytest.raises(RuntimeError, match=multipart_not_installed_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(username: str = Form(), password: str = Form()):
            return username  # pragma: nocover

        builder.build(router)


def test_no_multipart_installed_form_file(monkeypatch):
    monkeypatch.delattr("multipart.__version__", raising=False)
    with pytest.raises(RuntimeError, match=multipart_not_installed_error):
        router = ModuleRouter()

        @router.post("/")
        async def root(username: str = Form(), f: UploadFile = File()):
            return username  # pragma: nocover

        builder.build(router)
