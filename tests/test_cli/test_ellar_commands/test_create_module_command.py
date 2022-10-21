import os

from ellar.cli.service import EllarCLIService


def test_create_module_fails_for_py_project_none(cli_runner):
    result = cli_runner.invoke_ellar_command(["create-module", "testing_new_module"])
    assert result.exit_code == 1
    assert result.output == "Error: No pyproject.toml file found.\n"


def test_create_module_fails_if_no_project_is_found(cli_runner, write_empty_py_project):
    result = cli_runner.invoke_ellar_command(["create-module", "testing_new_module"])
    assert result.exit_code == 1
    assert result.output == (
        "Error: No available project found. please create ellar project with `ellar create-project 'project-name'`\n"
    )


def test_create_module_fails_for_invalid_module_name(
    cli_runner, write_empty_py_project
):
    result = cli_runner.invoke_ellar_command(["create-project", "testing_new_project"])
    assert result.exit_code == 0
    result = cli_runner.invoke_ellar_command(["create-module", "testing-new-module"])
    assert result.exit_code == 1
    assert result.output == (
        "Error: 'testing-new-module' is not a valid module-name. "
        "Please make sure the module-name is a valid identifier.\n"
    )


def test_create_module_fails_for_existing_module_project_name(
    cli_runner, write_empty_py_project
):
    result = cli_runner.invoke_ellar_command(
        ["create-project", "testing_new_project_two"]
    )
    assert result.exit_code == 0
    ellar_cli_service = EllarCLIService.import_project_meta("testing_new_project_two")
    module_name = "new_module_name"
    with open(
        os.path.join(ellar_cli_service.get_apps_module_path(), module_name + ".py"),
        mode="w",
    ) as fp:
        fp.write("")

    result = cli_runner.invoke_ellar_command(
        ["--project=testing_new_project_two", "create-module", module_name]
    )
    assert result.exit_code == 1
    assert result.output == (
        "Error: 'new_module_name' conflicts with the name of an existing "
        "Python module and cannot be used as a module-name. Please try another module-name.\n"
    )


def test_create_module_fails_for_existing_directory_name(
    tmpdir, cli_runner, write_empty_py_project
):
    result = cli_runner.invoke_ellar_command(
        ["create-project", "testing_new_project_three"]
    )
    assert result.exit_code == 0
    ellar_cli_service = EllarCLIService.import_project_meta("testing_new_project_three")
    module_name = "new_module_the_same_directory_name"
    os.makedirs(
        os.path.join(ellar_cli_service.get_apps_module_path(), module_name),
        exist_ok=True,
    )

    result = cli_runner.invoke_ellar_command(
        ["--project=testing_new_project_three", "create-module", module_name]
    )
    assert result.exit_code == 1
    assert result.output == (
        "Error: 'new_module_the_same_directory_name' conflicts with the name of an existing "
        "Python module and cannot be used as a module-name. Please try another module-name.\n"
    )


def test_create_module_works(tmpdir, process_runner, write_empty_py_project):
    result = process_runner(["ellar", "create-project", "test_project_new_module"])
    assert result.returncode == 0

    result = process_runner(
        [
            "ellar",
            "--project=test_project_new_module",
            "create-module",
            "test_new_module",
        ]
    )
    assert result.returncode == 0
    assert result.stdout == b"test_new_module module completely scaffolded\n"

    ellar_cli_service = EllarCLIService.import_project_meta("test_project_new_module")
    module_path = os.path.join(
        ellar_cli_service.get_apps_module_path(), "test_new_module"
    )
    files = os.listdir(module_path)

    for file in [
        "module.py",
        "tests",
        "routers.py",
        "services.py",
        "controllers.py",
        "schemas.py",
        "__init__.py",
    ]:
        assert file in files

    module_test_path = os.path.join(
        ellar_cli_service.get_apps_module_path(), "test_new_module", "tests"
    )
    test_files = os.listdir(module_test_path)
    for file in ["test_routers.py", "test_services.py", "test_controllers.py"]:
        assert file in test_files
