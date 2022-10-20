import typing as t

from jinja2 import Environment

from ellar.cli.file_scaffolding import FileTemplateScaffold
from ellar.cli.service import EllarCLIService
from ellar.core.schema import EllarScaffoldSchema


class DummyFileScaffolding(FileTemplateScaffold):
    def __init__(self, *args, **kwargs):
        self._validate_project_name_called = False
        self._on_scaffold_completed_called = False
        self._on_scaffold_started_called = False
        self._create_directory_called = False
        self._create_file_called = False
        super(DummyFileScaffolding, self).__init__(*args, **kwargs)

    def get_scaffolding_context(self, working_project_name: str):
        return dict(whatever_name=working_project_name)

    def validate_project_name(self) -> None:
        self._validate_project_name_called = True

    def on_scaffold_completed(self) -> None:
        self._on_scaffold_completed_called = True

    def on_scaffold_started(self) -> None:
        self._on_scaffold_started_called = True

    def create_directory(
        self, file, scaffold_ellar_template_path, working_directory
    ) -> None:
        self._create_directory_called = True
        super().create_directory(file, scaffold_ellar_template_path, working_directory)

    def create_file(self, base_path: str, file_name: str, content: t.Any) -> None:
        self._create_file_called = True

    def read_file_content(cls, path: str) -> str:
        return "whatever content {{whatever|title}}"


def test_validation_executed(tmp_path, write_empty_py_project):
    ellar_cli_service = EllarCLIService.import_project_meta()
    dummy = DummyFileScaffolding(
        working_directory=str(tmp_path),
        working_project_name="dummy",
        scaffold_ellar_template_root_path=str(tmp_path),
        schema=EllarScaffoldSchema.schema_example(),
        ellar_cli_service=ellar_cli_service,
    )
    assert dummy._validate_project_name_called
    assert isinstance(dummy._ctx.environment, Environment)
    assert dummy._ctx == dict(whatever_name="dummy")


def test_on_scaffold_completed_on_scaffold_started_and_create_directory_executed(
    tmp_path, write_empty_py_project
):
    ellar_cli_service = EllarCLIService.import_project_meta()
    dummy = DummyFileScaffolding(
        working_directory=str(tmp_path),
        working_project_name="dummy",
        scaffold_ellar_template_root_path=str(tmp_path),
        schema=EllarScaffoldSchema.schema_example(),
        ellar_cli_service=ellar_cli_service,
    )
    dummy.scaffold()
    assert dummy._on_scaffold_completed_called is True
    assert dummy._on_scaffold_started_called is True
    assert dummy._create_directory_called is True
    assert dummy._create_file_called is True
