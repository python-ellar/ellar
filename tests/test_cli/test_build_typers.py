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


def test_help_command(cli_runner):
    os.chdir(sample_app_path)
    result = subprocess.run(["ellar", "--help"], stdout=subprocess.PIPE)
    assert result.returncode == 0
    assert (
        result.stdout
        == b"Usage: Ellar, Python Web framework [OPTIONS] COMMAND [ARGS]...\n\nOptions:\n  -p, --project TEXT              Run Specific Command on a specific project\n  --install-completion [bash|zsh|fish|powershell|pwsh]\n                                  Install completion for the specified shell.\n  --show-completion [bash|zsh|fish|powershell|pwsh]\n                                  Show completion for the specified shell, to\n                                  copy it or customize the installation.\n  --help                          Show this message and exit.\n\nCommands:\n  create-module      - Scaffolds Ellar Application Module -\n  create-project     - Scaffolds Ellar Application -\n  db\n  runserver          - Starts Uvicorn Server -\n  say-hi\n  whatever-you-want  Whatever you want\n"
    )
    result = subprocess.run(
        ["ellar", "-p", "example_project", "--help"], stdout=subprocess.PIPE
    )
    assert result.returncode == 0
    assert (
        result.stdout
        == b"Usage: Ellar, Python Web framework [OPTIONS] COMMAND [ARGS]...\n\nOptions:\n  -p, --project TEXT              Run Specific Command on a specific project\n  --install-completion [bash|zsh|fish|powershell|pwsh]\n                                  Install completion for the specified shell.\n  --show-completion [bash|zsh|fish|powershell|pwsh]\n                                  Show completion for the specified shell, to\n                                  copy it or customize the installation.\n  --help                          Show this message and exit.\n\nCommands:\n  create-module      - Scaffolds Ellar Application Module -\n  create-project     - Scaffolds Ellar Application -\n  db\n  runserver          - Starts Uvicorn Server -\n  say-hi\n  whatever-you-want  Whatever you want\n"
    )

    result = subprocess.run(
        ["ellar", "-p", "example_project_2", "--help"], stdout=subprocess.PIPE
    )
    assert result.returncode == 0
    assert (
        result.stdout
        == b"Usage: Ellar, Python Web framework [OPTIONS] COMMAND [ARGS]...\n\nOptions:\n  -p, --project TEXT              Run Specific Command on a specific project\n  --install-completion [bash|zsh|fish|powershell|pwsh]\n                                  Install completion for the specified shell.\n  --show-completion [bash|zsh|fish|powershell|pwsh]\n                                  Show completion for the specified shell, to\n                                  copy it or customize the installation.\n  --help                          Show this message and exit.\n\nCommands:\n  create-module      - Scaffolds Ellar Application Module -\n  create-project     - Scaffolds Ellar Application -\n  db\n  project-2-command  Project 2 Custom Command\n  runserver          - Starts Uvicorn Server -\n  say-hi\n  whatever-you-want  Whatever you want\n"
    )
