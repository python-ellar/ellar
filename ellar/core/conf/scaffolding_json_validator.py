import os

from ellar.core import conf
from ellar.core.schema import EllarScaffoldList, EllarScaffoldSchema
from ellar.helper.module_loading import module_dir

_conf_module_dir = module_dir(conf)
_module_template_json = os.path.join(_conf_module_dir, "module_template", "setup.json")
_project_template_json = os.path.join(
    _conf_module_dir, "project_template", "setup.json"
)

SCAFFOLDING_TEMPLATES = [
    (os.path.join(_conf_module_dir, "module_template"), _module_template_json),
    (os.path.join(_conf_module_dir, "project_template"), _project_template_json),
]


class ScaffoldingJSONValidator:
    def __init__(self, root_path: str, json_path: str) -> None:
        self._json_path = json_path
        self._root_path = root_path
        self._schema: EllarScaffoldSchema = EllarScaffoldSchema.parse_file(json_path)

    def validate_json(self) -> None:
        for file in self._schema.files:
            self._check_directory_file_exist(
                file,
                scaffold_ellar_template_path=self._root_path,
            )

    def _check_directory_file_exist(
        self, file: EllarScaffoldList, scaffold_ellar_template_path: str
    ) -> None:
        scaffold_template_path = os.path.join(scaffold_ellar_template_path, file.name)

        if file.is_directory:
            if not os.path.isdir(scaffold_template_path):
                raise Exception(
                    f"Scaffolding Folder: {file.name} @{scaffold_ellar_template_path} is not a Directory"
                )

            for file in file.files or []:
                self._check_directory_file_exist(
                    file=file,
                    scaffold_ellar_template_path=scaffold_template_path,
                )
        else:
            if not os.path.exists(scaffold_template_path):
                raise Exception(
                    f"Scaffolding File: {scaffold_template_path} Does not exist"
                )


if __name__ == "__main__":
    for path in SCAFFOLDING_TEMPLATES:
        validator = ScaffoldingJSONValidator(*path)
        validator.validate_json()
