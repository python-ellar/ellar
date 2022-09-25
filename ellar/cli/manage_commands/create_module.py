import os
import typing as t

import typer

from ellar.constants import ELLAR_META
from ellar.core import conf
from ellar.helper.module_loading import module_dir

from ...cli.schema import EllarScaffoldSchema
from ...cli.service import EllarCLIService
from ..file_scaffolding import FileTemplateScaffold

__all__ = ["create_module"]

conf_module_dir = module_dir(conf)
root_scaffold_template_path = os.path.join(conf_module_dir, "module_template")
module_template_json = os.path.join(root_scaffold_template_path, "setup.json")


class ModuleTemplateScaffold(FileTemplateScaffold):
    def on_scaffold_completed(self) -> None:
        print(f"{self._working_project_name} module completely scaffolded")

    def validate_project_name(self) -> None:
        if not self._working_project_name.isidentifier():
            print(
                "'{name}' is not a valid {app} {type}. Please make sure the "
                "{type} is a valid identifier.".format(
                    name=self._working_project_name,
                    app="module",
                    type="name",
                )
            )
            raise typer.Abort()

        dirs_ = next(os.walk(self._working_directory))[1]

        if self._working_project_name in dirs_:
            print("Module Project already exist.")
            raise typer.Abort()

    def get_scaffolding_context(self, working_project_name: str) -> t.Dict:
        template_context = dict(module_name=working_project_name)
        return template_context


def create_module(ctx: typer.Context, module_name: str):
    """- Scaffolds Ellar Application Module -"""

    ellar_project_meta = t.cast(t.Optional[EllarCLIService], ctx.meta.get(ELLAR_META))
    if not ellar_project_meta:
        print("No pyproject.toml file found.")
        raise typer.Abort()

    schema = EllarScaffoldSchema.parse_file(module_template_json)
    project_template_scaffold = ModuleTemplateScaffold(
        schema=schema,
        working_directory=ellar_project_meta.get_apps_module_path(),
        scaffold_ellar_template_root_path=root_scaffold_template_path,
        ellar_project_meta=ellar_project_meta,
        working_project_name=module_name.lower(),
    )
    project_template_scaffold.scaffold()
