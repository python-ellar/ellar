import functools
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from uuid import uuid4

import click.testing
import pytest
from ellar.reflect import reflect
from pydantic import create_model
from starlette.testclient import TestClient


@pytest.fixture
def test_client_factory(anyio_backend_name, anyio_backend_options):
    # anyio_backend_name defined by:
    # https://anyio.readthedocs.io/en/stable/testing.html#specifying-the-backends-to-run-on
    return functools.partial(
        TestClient,
        backend=anyio_backend_name,
        backend_options=anyio_backend_options,
    )


@pytest.fixture(
    name="model_with_path", params=[PurePath, PurePosixPath, PureWindowsPath]
)
def fixture_model_with_path(request):
    model_with_path = create_model(
        "ModelWithPath",
        path=(request.param, ...),
        __config__={"arbitrary_types_allowed": True},  # type: ignore
    )
    return model_with_path(path=request.param("/foo", "bar"))


@pytest.fixture
def random_type():
    return type(f"Random{uuid4().hex[:6]}", (), {})


@pytest.fixture
def cli_runner():
    return click.testing.CliRunner()


@pytest.fixture
def reflect_context():
    with reflect.context():
        yield


@pytest.fixture
async def async_reflect_context():
    async with reflect.async_context():
        yield
