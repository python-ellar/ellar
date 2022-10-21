from tomlkit import table
from tomlkit.items import Table

from ellar.cli.service import EllarPyProject
from ellar.constants import ELLAR_PY_PROJECT


def test_get_or_create_ellar_py_project(mock_py_project_table):
    assert ELLAR_PY_PROJECT not in mock_py_project_table
    EllarPyProject.get_or_create_ellar_py_project(mock_py_project_table)
    assert ELLAR_PY_PROJECT in mock_py_project_table

    new_py_project_table = table()
    ellar = table()
    ellar.update({"not_a_new_instance": True})
    new_py_project_table.add(ELLAR_PY_PROJECT, ellar)

    ellar_py_project = EllarPyProject.get_or_create_ellar_py_project(
        new_py_project_table
    )
    assert ellar_py_project.get_root_node() is ellar
    assert "not_a_new_instance" in ellar_py_project.get_root_node()


def test_has_default_project(ellar_py_project):
    assert ellar_py_project.has_default_project is False

    ellar_py_project.default_project = "testing default"
    assert ellar_py_project.has_default_project is True


def test_default_project(ellar_py_project):
    assert ellar_py_project.default_project is None

    ellar_py_project.default_project = "testing default"
    assert ellar_py_project.default_project == "testing default"


def test_get_projects(ellar_py_project):
    assert isinstance(ellar_py_project.get_projects(), Table)
    ellar_py_project.get_or_create_project("newProject")
    projects = ellar_py_project.get_projects()
    assert "newProject".lower() in projects


def test_get_project_by_name(ellar_py_project):
    new_project = ellar_py_project.get_or_create_project("newProject")
    assert ellar_py_project.get_project("newProject".lower()) is new_project


def test_check_if_project_exist(ellar_py_project):
    ellar_py_project.get_or_create_project("newProject")
    assert ellar_py_project.has_project("newProject".lower())

    assert ellar_py_project.has_project("newProject2") is False


def test_get_root_node(mock_py_project_table):
    ellar_py_project = EllarPyProject.get_or_create_ellar_py_project(
        mock_py_project_table
    )
    assert ellar_py_project.get_root_node() is mock_py_project_table.get(
        ELLAR_PY_PROJECT
    )
