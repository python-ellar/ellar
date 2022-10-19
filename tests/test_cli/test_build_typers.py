import os
import subprocess
from pathlib import Path

sample_app_path = os.path.join(Path(__file__).parent, "sample_app")


def test_build_typers_ellar_typer_works_for_default_project(cli_runner):
    os.chdir(sample_app_path)
    result = subprocess.run(["ellar", "db", "create-migration"], stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout == b"create migration command\n"


def test_build_typers_command_works_for_default_project(cli_runner):
    os.chdir(sample_app_path)
    result = subprocess.run(["ellar", "whatever-you-want"], stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout == b"Whatever you want command\n"


def test_build_typers_ellar_typer_for_specific_project_works():
    os.chdir(sample_app_path)
    result = subprocess.run(
        ["ellar", "-p", "example_project_2", "db", "create-migration"],
        stdout=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout == b"create migration command from example_project_2\n"

    result = subprocess.run(
        ["ellar", "--project", "example_project_2", "db", "create-migration"],
        stdout=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout == b"create migration command from example_project_2\n"


def test_build_typers_command_for_specific_project_works():
    os.chdir(sample_app_path)

    result = subprocess.run(
        ["ellar", "-p", "example_project_2", "whatever-you-want"],
        stdout=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout == b"Whatever you want command from example_project_2\n"

    result = subprocess.run(
        ["ellar", "-p", "example_project_2", "whatever-you-want"],
        stdout=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout == b"Whatever you want command from example_project_2\n"
