import contextlib
import functools
import socket
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


def _unused_port(socket_type: int) -> int:
    """Find an unused localhost port from 1024-65535 and return it."""
    with contextlib.closing(socket.socket(type=socket_type)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# This was copied from pytest-asyncio.
# Ref.: https://github.com/pytest-dev/pytest-asyncio/blob/25d9592286682bc6dbfbf291028ff7a9594cf283/pytest_asyncio/plugin.py#L525-L527
@pytest.fixture
def unused_tcp_port() -> int:
    return _unused_port(socket.SOCK_STREAM)
