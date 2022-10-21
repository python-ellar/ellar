import functools
import os.path
import subprocess
import sys
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from uuid import uuid4

import pytest
from pydantic import create_model
from starlette.testclient import TestClient
from tomlkit import table

from ellar.cli.service import PY_PROJECT_TOML, EllarCLIService, EllarPyProject
from ellar.cli.testing import EllarCliRunner


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
    class Config:
        arbitrary_types_allowed = True

    model_with_path = create_model(
        "ModelWithPath", path=(request.param, ...), __config__=Config  # type: ignore
    )
    return model_with_path(path=request.param("/foo", "bar"))


@pytest.fixture
def random_type():
    return type(f"Random{uuid4().hex[:6]}", (), {})


@pytest.fixture
def mock_py_project_table():
    return table()


@pytest.fixture
def ellar_py_project(mock_py_project_table):
    return EllarPyProject.get_or_create_ellar_py_project(mock_py_project_table)


@pytest.fixture
def add_ellar_project_to_py_project(ellar_py_project, tmp_py_project_path, tmp_path):
    EllarCLIService.write_py_project(
        tmp_py_project_path, ellar_py_project.get_root_node()
    )

    def _wrapper(project_name: str):
        cli_service = EllarCLIService(
            py_project_path=tmp_py_project_path,
            ellar_py_projects=ellar_py_project,
            cwd=str(tmp_path),
        )
        cli_service.create_ellar_project_meta(project_name)
        return ellar_py_project

    return _wrapper


@pytest.fixture
def write_empty_py_project(tmp_py_project_path, mock_py_project_table):
    EllarCLIService.write_py_project(tmp_py_project_path, mock_py_project_table)
    return mock_py_project_table


@pytest.fixture
def tmp_py_project_path(tmp_path):
    os.chdir(str(tmp_path))
    py_project_toml = tmp_path / PY_PROJECT_TOML
    py_project_toml.touch(exist_ok=True)
    return py_project_toml


@pytest.fixture(autouse=True)
def sys_path(tmp_path):
    sys.path.append(str(tmp_path))
    yield
    sys.path.remove(str(tmp_path))


@pytest.fixture
def cli_runner(tmp_path):
    os.chdir(str(tmp_path))
    return EllarCliRunner()


@pytest.fixture
def process_runner(tmp_path):
    os.chdir(str(tmp_path))

    def _wrapper_process(*args, **kwargs):
        kwargs.setdefault("stdout", subprocess.PIPE)
        kwargs.setdefault("stderr", subprocess.PIPE)
        result = subprocess.run(*args, **kwargs)
        return result

    return _wrapper_process
