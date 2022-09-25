import os
import typing as t
import uuid

import typer

from ellar.constants import ELLAR_META
from ellar.core import conf
from ellar.helper.module_loading import module_dir

from ...cli.schema import EllarScaffoldSchema
from ...cli.service import EllarCLIService
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

    def on_scaffold_completed(self) -> None:
        self.ellar_project_meta.create_ellar_project_meta(
            project_name=self._working_project_name
        )
        print(
            f"{self._working_project_name} project scaffold completed. Please on the below"
        )
        print(f"ellar --project {self._working_project_name} runserver --reload")
        print("Happy coding!")


def create_project(ctx: typer.Context, project_name: str):
    """- Scaffolds Ellar Application -"""

    ellar_project_meta = t.cast(t.Optional[EllarCLIService], ctx.meta.get(ELLAR_META))
    if not ellar_project_meta:
        print("No pyproject.toml file found.")
        raise typer.Abort()

    if ellar_project_meta.ellar_py_projects.has_project(project_name):
        print("Ellar Project already exist.")
        raise typer.Abort()

    schema = EllarScaffoldSchema.parse_file(project_template_json)
    project_template_scaffold = ProjectTemplateScaffold(
        schema=schema,
        working_directory=os.getcwd(),
        scaffold_ellar_template_root_path=root_scaffold_template_path,
        ellar_project_meta=ellar_project_meta,
        working_project_name=project_name.lower(),
    )
    project_template_scaffold.scaffold()
