import os
import typing as t
from abc import abstractmethod

from jinja2 import Environment

from ellar.core.schema import EllarScaffoldList, EllarScaffoldSchema

from .service import EllarCLIService

__all__ = ["FileTemplateScaffold"]


class ProjectScaffoldContext(dict):
    def __init__(self, environment: Environment, **kwargs):
        super().__init__(kwargs)
        self.environment = environment
        self.environment.globals.update(kwargs)


class FileTemplateScaffold:
    def __init__(
        self,
        *,
        schema: EllarScaffoldSchema,
        working_project_name: str,
        working_directory: str,
        scaffold_ellar_template_root_path: str,
        ellar_cli_service: EllarCLIService,
    ):
        self._schema = schema
        self._working_project_name = working_project_name
        self._ctx = ProjectScaffoldContext(
            Environment(), **self.get_scaffolding_context(working_project_name)
        )
        self._working_directory = working_directory
        self._scaffold_ellar_template_root_path = scaffold_ellar_template_root_path
        self.ellar_cli_service = ellar_cli_service
        self.validate_project_name()

    def get_scaffolding_context(self, working_project_name: str) -> t.Dict:
        return {}

    @classmethod
    def read_file_content(cls, path: str) -> str:
        with open(path, mode="r") as fp:
            return fp.read()

    def create_root_path(self) -> str:
        root_dir = os.path.join(
            self._working_directory, self._working_project_name.lower()
        )
        os.mkdir(root_dir)
        return root_dir

    def create_file(self, base_path: str, file_name: str, content: t.Any) -> None:
        with open(
            os.path.join(base_path, file_name.replace("ellar", "py")), mode="w"
        ) as fw:
            refined_content = self._ctx.environment.from_string(content).render()
            fw.writelines(refined_content)

    def scaffold(self) -> None:
        self.on_scaffold_started()
        for file in self._schema.files:
            self.create_directory(
                file,
                scaffold_ellar_template_path=self._scaffold_ellar_template_root_path,
                working_directory=self._working_directory,
            )
        self.on_scaffold_completed()

    def on_scaffold_completed(self) -> None:
        pass

    def on_scaffold_started(self) -> None:
        for context in self._schema.context:
            assert self._ctx[context], f"{context} template context is missing."

    def create_directory(
        self, file: EllarScaffoldList, scaffold_ellar_template_path, working_directory
    ) -> None:
        name = file.name
        if name in self._ctx:
            name = self._ctx.get(file.name, file.name)

        scaffold_template_path = os.path.join(scaffold_ellar_template_path, file.name)

        if file.is_directory:
            new_scaffold_dir = os.path.join(working_directory, name)
            os.makedirs(new_scaffold_dir, exist_ok=True)
            for file in file.files or []:
                self.create_directory(
                    file=file,
                    working_directory=new_scaffold_dir,
                    scaffold_ellar_template_path=scaffold_template_path,
                )
        else:
            content = self.read_file_content(scaffold_template_path)
            self.create_file(
                base_path=working_directory, file_name=name, content=content
            )

    @abstractmethod
    def validate_project_name(self) -> None:
        # Check it's a valid directory name.
        pass
