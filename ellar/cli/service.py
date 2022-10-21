import os
import typing as t

from click import ClickException
from tomlkit import dumps as tomlkit_dumps, parse as tomlkit_parse, table
from tomlkit.items import Table

from ellar.constants import ELLAR_PY_PROJECT
from ellar.core import App, Config, ModuleBase, schema
from ellar.core.schema import EllarPyProjectSerializer
from ellar.helper.importer import import_from_string, module_import
from ellar.helper.module_loading import module_dir

PY_PROJECT_TOML = "pyproject.toml"
ELLAR_DEFAULT_KEY = "default"
ELLAR_PROJECTS_KEY = "projects"


class EllarCLIException(ClickException):
    pass


class EllarPyProject:
    def __init__(self, ellar: Table = None) -> None:
        self._ellar = ellar if ellar is not None else table()
        self._projects = self._ellar.setdefault(ELLAR_PROJECTS_KEY, table())
        self._default_project = self._ellar.get(ELLAR_DEFAULT_KEY, None)

    @classmethod
    def get_or_create_ellar_py_project(
        cls, py_project_table: Table
    ) -> "EllarPyProject":
        ellar_py_project_table = py_project_table.setdefault(ELLAR_PY_PROJECT, table())
        return cls(ellar_py_project_table)

    @property
    def has_default_project(self) -> bool:
        return self._ellar.get(ELLAR_DEFAULT_KEY, None) is not None

    @property
    def default_project(self) -> str:
        return self._ellar.get(ELLAR_DEFAULT_KEY, None)

    @default_project.setter
    def default_project(self, value: str) -> None:
        self._ellar.update(default=value)

    def get_projects(self) -> Table:
        return self._projects

    def get_project(self, project_name: str) -> Table:
        return self._projects.get(project_name)

    def get_or_create_project(self, project_name: str) -> Table:
        project = self._projects.setdefault(project_name.lower(), table())
        return project

    def has_project(self, project_name: t.Optional[str]) -> bool:
        if not project_name:
            return False
        return project_name in self._projects

    def get_root_node(self) -> Table:
        return self._ellar


class EllarCLIService:
    schema_cls: t.Type[schema.Serializer] = EllarPyProjectSerializer

    def __init__(
        self,
        *,
        meta: t.Optional[EllarPyProjectSerializer] = None,
        py_project_path: str,
        cwd: str,
        app_name: str = "ellar",
        ellar_py_projects: EllarPyProject = None,
    ) -> None:
        self._meta = meta
        self.py_project_path = py_project_path
        self.cwd = cwd
        self.app = app_name
        self.ellar_py_projects = ellar_py_projects or EllarPyProject()

    @property
    def has_meta(self) -> bool:
        return self._meta is not None

    @property
    def project_meta(self) -> t.Optional[EllarPyProjectSerializer]:
        return self._meta

    @classmethod
    def cwd_has_pyproject_file(cls) -> bool:
        cwd = os.getcwd()
        py_project_file_path = os.path.join(cwd, PY_PROJECT_TOML)
        return os.path.exists(py_project_file_path)

    @classmethod
    def import_project_meta(
        cls, project: t.Optional[str] = None
    ) -> t.Optional["EllarCLIService"]:
        cwd = os.getcwd()
        project_to_load: t.Optional[str] = None
        ellar_py_projects = None

        py_project_file_path = os.path.join(cwd, PY_PROJECT_TOML)
        if os.path.exists(py_project_file_path):

            pyproject_table = EllarCLIService.read_py_project(py_project_file_path)
            _ellar_pyproject_serializer: t.Optional[EllarPyProjectSerializer] = None

            if pyproject_table and ELLAR_PY_PROJECT in pyproject_table:
                ellar_py_projects = EllarPyProject(
                    pyproject_table.get(ELLAR_PY_PROJECT)
                )
                if ellar_py_projects.has_project(
                    project
                ) or ellar_py_projects.has_project(ellar_py_projects.default_project):
                    project_to_load = (
                        project
                        if ellar_py_projects.has_project(project)
                        else ellar_py_projects.default_project
                    )

                    _ellar_pyproject_serializer = t.cast(
                        EllarPyProjectSerializer,
                        cls.schema_cls.parse_obj(
                            ellar_py_projects.get_project(project_to_load)
                        ),
                    )

            return cls(
                meta=_ellar_pyproject_serializer,
                py_project_path=py_project_file_path,
                cwd=cwd,
                app_name=project_to_load,
                ellar_py_projects=ellar_py_projects,
            )

    def create_ellar_project_meta(self, project_name: str) -> None:
        pyproject_table = EllarCLIService.read_py_project(self.py_project_path)
        if pyproject_table is None:
            raise EllarCLIException("Could not locate `pyproject.toml`")

        ellar_py_project = self.ellar_py_projects.get_or_create_ellar_py_project(
            pyproject_table
        )

        if ellar_py_project.has_project(project_name.lower()):
            raise EllarCLIException(
                f"project -> `{project_name}` already exist in ellar projects"
            )

        if not ellar_py_project.has_default_project:
            ellar_py_project.default_project = project_name.lower()

        ellar_new_project = ellar_py_project.get_or_create_project(project_name.lower())
        ellar_new_project.add("project-name", project_name.lower())
        ellar_new_project.add("application", f"{project_name}.server:application")
        ellar_new_project.add("config", f"{project_name}.config:DevelopmentConfig")
        ellar_new_project.add(
            "root-module", f"{project_name}.root_module:ApplicationModule"
        )
        ellar_new_project.add("apps-module", f"{project_name}.apps")

        # TODO: lock pyproject.toml file
        EllarCLIService.write_py_project(self.py_project_path, pyproject_table)

    @staticmethod
    def read_py_project(path: str) -> t.Optional[Table]:
        if os.path.exists(path):
            with open(path, mode="r") as fp:
                table_content = tomlkit_parse(fp.read())
                return table_content

    @staticmethod
    def write_py_project(path: str, content: Table) -> None:
        with open(path, mode="w") as fw:
            fw.writelines(tomlkit_dumps(content))

    def import_application(self) -> "App":
        application_module = import_from_string(self._meta.application)
        return application_module

    def import_configuration(self) -> t.Type["Config"]:
        config = import_from_string(self._meta.config)
        return config

    def get_application_config(self) -> "Config":
        config = Config(self._meta.config)
        return config

    def import_root_module(self) -> t.Type["ModuleBase"]:
        root_module = import_from_string(self._meta.root_module)
        return root_module

    def import_apps_module(self) -> t.Any:
        apps_module = module_import(self._meta.apps_module)
        return apps_module

    def get_apps_module_path(self) -> str:
        apps_module = self.import_apps_module()
        return module_dir(apps_module)
