import os

from ellar.cli.service import EllarCLIService
from ellar.core import App


def test_create_project_fails_for_py_project_none(cli_runner):
    result = cli_runner.invoke_ellar_command(["create-project", "testing_new_project"])
    assert result.exit_code == 1
    assert result.output == "Error: No pyproject.toml file found.\n"


def test_create_project_fails_for_existing_project_name(
    cli_runner, add_ellar_project_to_py_project
):
    add_ellar_project_to_py_project("testing_new_project")
    result = cli_runner.invoke_ellar_command(["create-project", "testing_new_project"])
    assert result.exit_code == 1
    assert result.output == "Error: Ellar Project already exist.\n"


def test_create_project_fails_for_invalid_project_name(
    cli_runner, write_empty_py_project
):
    result = cli_runner.invoke_ellar_command(["create-project", "testing-new-project"])
    assert result.exit_code == 1
    assert result.output == (
        "Error: 'testing-new-project' is not a valid project-name. "
        "Please make sure the project-name is a valid identifier.\n"
    )


def test_create_project_fails_for_existing_module_project_name(
    tmpdir, cli_runner, write_empty_py_project
):
    module_name = "new_project_module"
    with open(os.path.join(tmpdir, module_name + ".py"), mode="w") as fp:
        fp.write("")

    result = cli_runner.invoke_ellar_command(["create-project", module_name])
    assert result.exit_code == 1
    assert result.output == (
        "Error: 'new_project_module' conflicts with the name of an existing "
        "Python module and cannot be used as a project-name. Please try another project-name.\n"
    )


def test_create_project_command_works(tmpdir, cli_runner, write_empty_py_project):
    result = cli_runner.invoke_ellar_command(["create-project", "ellar_project"])
    assert result.exit_code == 0
    assert result.output == (
        "`ellar_project` project scaffold completed. To start your server, run the command below\n"
        "ellar --project ellar_project runserver --reload\n"
        "Happy coding!\n"
    )
    ellar_cli_service = EllarCLIService.import_project_meta()
    assert ellar_cli_service._meta.dict() == {
        "project_name": "ellar_project",
        "application": "ellar_project.server:application",
        "config": "ellar_project.config:DevelopmentConfig",
        "root_module": "ellar_project.root_module:ApplicationModule",
        "apps_module": "ellar_project.apps",
    }

    application = ellar_cli_service.import_application()
    assert isinstance(application, App)
