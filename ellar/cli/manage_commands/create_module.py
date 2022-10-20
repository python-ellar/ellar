import os
import sys
import typing as t
from importlib import import_module

import typer

from ellar.constants import ELLAR_META
from ellar.core import conf
from ellar.core.schema import EllarScaffoldSchema
from ellar.helper.module_loading import module_dir

from ...cli.service import EllarCLIException, EllarCLIService
from ..file_scaffolding import FileTemplateScaffold

__all__ = ["create_module"]

conf_module_dir = module_dir(conf)
root_scaffold_template_path = os.path.join(conf_module_dir, "module_template")
module_template_json = os.path.join(root_scaffold_template_path, "setup.json")


class ModuleTemplateScaffold(FileTemplateScaffold):
    def on_scaffold_completed(self) -> None:
        print(f"{self._working_project_name} module completely scaffolded")

    def validate_project_name(self) -> None:
        working_directory_in_sys_path = False
        if self._working_directory in sys.path:
            working_directory_in_sys_path = True

        if not self._working_project_name.isidentifier():
            message = (
                f"'{self._working_project_name}' is not a valid module-name. "
                f"Please make sure the module-name is a valid identifier."
            )
            raise EllarCLIException(message)

        try:
            if not working_directory_in_sys_path:
                sys.path.append(self._working_directory)
            import_module(self._working_project_name)
        except ImportError:
            pass
        else:
            message = (
                "'{name}' conflicts with the name of an existing Python "
                "module and cannot be used as a module-name. Please try another module-name.".format(
                    name=self._working_project_name
                )
            )
            raise EllarCLIException(message)
        finally:
            if not working_directory_in_sys_path:
                sys.path.remove(self._working_directory)

    def get_scaffolding_context(self, working_project_name: str) -> t.Dict:
        template_context = dict(module_name=working_project_name)
        return template_context


def create_module(ctx: typer.Context, module_name: str):
    """- Scaffolds Ellar Application Module -"""

    ellar_project_meta = t.cast(t.Optional[EllarCLIService], ctx.meta.get(ELLAR_META))
    if not ellar_project_meta:
        raise EllarCLIException("No pyproject.toml file found.")

    if not ellar_project_meta.has_meta:
        raise EllarCLIException(
            "No available project found. please create ellar project with `ellar create-project 'project-name'`"
        )

    schema = EllarScaffoldSchema.parse_file(module_template_json)
    project_template_scaffold = ModuleTemplateScaffold(
        schema=schema,
        working_directory=ellar_project_meta.get_apps_module_path(),
        scaffold_ellar_template_root_path=root_scaffold_template_path,
        ellar_cli_service=ellar_project_meta,
        working_project_name=module_name.lower(),
    )
    project_template_scaffold.scaffold()
