import os
import typing as t
from pathlib import Path

from ellar.common.compatible import cached_property
from ellar.common.interfaces import IModuleTemplateLoader


class ModuleTemplating(IModuleTemplateLoader):
    _template_folder: t.Optional[str]
    _base_directory: t.Optional[t.Union[Path, str]]
    _static_folder: t.Optional[str]

    @property
    def template_folder(self) -> t.Optional[str]:
        return self._template_folder

    @property
    def root_path(self) -> t.Optional[t.Union[Path, str]]:
        return self._base_directory

    @cached_property
    def static_directory(self) -> t.Optional[str]:
        if self.root_path and self._static_folder:
            path = os.path.join(str(self.root_path), self._static_folder)
            if os.path.exists(path):
                return path
        return None
