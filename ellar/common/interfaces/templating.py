import os
import typing as t
from abc import abstractmethod
from pathlib import Path

from ellar.common.compatible import cached_property
from jinja2 import FileSystemLoader


class IModuleTemplateLoader:
    @property
    @abstractmethod
    def template_folder(self) -> t.Optional[str]:  # pragma: no cover
        """template folder name or template path"""

    @property
    @abstractmethod
    def root_path(self) -> t.Optional[t.Union[Path, str]]:
        """root template path"""

    @cached_property
    def jinja_loader(self) -> t.Optional[FileSystemLoader]:
        if (
            self.template_folder
            and self.root_path
            and os.path.exists(os.path.join(str(self.root_path), self.template_folder))
        ):
            return FileSystemLoader(
                os.path.join(str(self.root_path), self.template_folder)
            )
        else:
            return None
