import os
import typing as t
import uuid
from importlib import import_module

import typer

from ellar.constants import ELLAR_META
from ellar.core import conf
from ellar.core.schema import EllarScaffoldSchema
from ellar.helper.module_loading import module_dir

from ...cli.service import EllarCLIException, EllarCLIService
from ..file_scaffolding import FileTemplateScaffold

__all__ = ["create_project"]


conf_module_dir = module_dir(conf)
root_scaffold_template_path = os.path.join(conf_module_dir, "project_template")
project_template_json = os.path.join(root_scaffold_template_path, "setup.json")


class ProjectTemplateScaffold(FileTemplateScaffold):
    def get_scaffolding_context(self, working_project_name: str) -> t.Dict:
        template_context = dict(
            project_name=working_project_name, secret_key=f"ellar_{uuid.uuid4()}"
        )
        return template_context

    def validate_project_name(self) -> None:
        if not self._working_project_name.isidentifier():
            message = "'{name}' is not a valid project-name. Please make sure the project-name is a valid identifier.".format(
                name=self._working_project_name,
            )
            raise EllarCLIException(message)
        # Check it cannot be imported.
        try:
            import_module(self._working_project_name)
        except ImportError:
            pass
        else:
            message = (
                "'{name}' conflicts with the name of an existing Python "
                "module and cannot be used as a project-name. Please try another project-name.".format(
                    name=self._working_project_name
                )
            )
            raise EllarCLIException(message)

    def on_scaffold_completed(self) -> None:
        self.ellar_cli_service.create_ellar_project_meta(
            project_name=self._working_project_name
        )
        print(
            f"`{self._working_project_name}` project scaffold completed. To start your server, run the command below"
        )
        print(f"ellar --project {self._working_project_name} runserver --reload")
        print("Happy coding!")


def create_project(ctx: typer.Context, project_name: str):
    """- Scaffolds Ellar Application -"""

    ellar_project_meta = t.cast(t.Optional[EllarCLIService], ctx.meta.get(ELLAR_META))
    if not ellar_project_meta:
        raise EllarCLIException("No pyproject.toml file found.")

    if ellar_project_meta.ellar_py_projects.has_project(project_name):
        raise EllarCLIException("Ellar Project already exist.")

    schema = EllarScaffoldSchema.parse_file(project_template_json)
    project_template_scaffold = ProjectTemplateScaffold(
        schema=schema,
        working_directory=os.getcwd(),
        scaffold_ellar_template_root_path=root_scaffold_template_path,
        ellar_cli_service=ellar_project_meta,
        working_project_name=project_name.lower(),
    )
    project_template_scaffold.scaffold()
