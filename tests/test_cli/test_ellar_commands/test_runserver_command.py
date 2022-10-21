import importlib
import os
import sys
from unittest import mock

import pytest

from ellar.cli.service import EllarCLIService

HEADERS = "Content-Security-Policy:default-src 'self'; script-src https://example.com"
runserver = importlib.import_module("ellar.cli.manage_commands.runserver")


def test_runserver_command_fails_for_py_project_none(process_runner):
    result = process_runner(["ellar", "runserver"])
    assert result.returncode == 1
    assert result.stderr == b"Error: No pyproject.toml file found.\n"


def test_runserver_fails_if_no_project_is_found(process_runner, write_empty_py_project):
    result = process_runner(["ellar", "runserver"])
    assert result.returncode == 1
    assert result.stderr == (
        b"Error: No available project found. please create ellar project with `ellar create-project 'project-name'`\n"
    )


def test_runserver_command_works(cli_runner, process_runner, write_empty_py_project):
    process_runner(["ellar", "create-project", "ellar_project_1_0"])
    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(["runserver"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    ellar_cli_service = EllarCLIService.import_project_meta()
    assert mock_run.call_args[0] == (ellar_cli_service.project_meta.application,)


def test_cli_headers(
    tmpdir, cli_runner, process_runner, write_empty_py_project
) -> None:
    process_runner(["ellar", "create-project", "ellar_project_1"])
    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(["runserver", "--header", HEADERS])

    assert result.output == ""
    assert result.exit_code == 0
    mock_run.assert_called_once()
    assert mock_run.call_args[1]["headers"] == [
        [
            "Content-Security-Policy",
            "default-src 'self'; script-src https://example.com",
        ]
    ]


def test_cli_call_change_reload_run(
    tmpdir, cli_runner, process_runner, write_empty_py_project
) -> None:
    process_runner(["ellar", "create-project", "ellar_project_2"])
    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(["runserver", "--reload"])

    assert result.exit_code == 0
    mock_run.assert_called_once()
    assert mock_run.call_args[1]["reload"] is True


def test_cli_call_multiprocess_run(
    cli_runner, process_runner, write_empty_py_project
) -> None:
    process_runner(["ellar", "create-project", "ellar_project_3"])
    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(["runserver", "--workers=2"])

    assert result.exit_code == 0
    mock_run.assert_called_once()
    assert mock_run.call_args[1]["workers"] == 2


def test_cli_uds(
    tmp_path, cli_runner, process_runner, write_empty_py_project
) -> None:  # pragma: py-win32
    process_runner(["ellar", "create-project", "ellar_project_4"])
    uds_file = tmp_path / "uvicorn.sock"
    uds_file.touch(exist_ok=True)

    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(
            ["runserver", "--workers=2", "--uds", str(uds_file)]
        )

    assert result.exit_code == 0
    assert result.output == ""
    mock_run.assert_called_once()
    assert mock_run.call_args[1]["workers"] == 2
    assert mock_run.call_args[1]["uds"] == str(uds_file)


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Requires later version of Uvicorn"
)
def test_cli_event_size(cli_runner, process_runner, write_empty_py_project) -> None:
    process_runner(["ellar", "create-project", "ellar_project_5"])
    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(
            ["runserver", "--h11-max-incomplete-event-size", str(32 * 1024)]
        )
    assert result.output == ""
    assert result.exit_code == 0
    mock_run.assert_called_once()
    assert mock_run.call_args[1]["h11_max_incomplete_event_size"] == 32768


@pytest.fixture()
def load_env_h11_protocol():
    old_environ = dict(os.environ)
    os.environ["UVICORN_HTTP"] = "h11"
    yield
    os.environ.clear()
    os.environ.update(old_environ)


def test_env_variables(
    load_env_h11_protocol: None, process_runner, cli_runner, write_empty_py_project
):
    process_runner(["ellar", "create-project", "ellar_project_6"])
    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(["runserver"], env=os.environ)
    assert result.output == ""
    assert result.exit_code == 0
    _, kwargs = mock_run.call_args
    assert kwargs["http"] == "auto"


def test_mis_match_env_variables(
    load_env_h11_protocol: None, process_runner, cli_runner, write_empty_py_project
):
    process_runner(["ellar", "create-project", "ellar_project_7"])
    with mock.patch.object(runserver, "uvicorn_run") as mock_run:
        result = cli_runner.invoke_ellar_command(
            ["runserver", "--http=httptools"], env=os.environ
        )
    assert result.output == ""
    assert result.exit_code == 0
    _, kwargs = mock_run.call_args
    assert kwargs["http"] == "httptools"
