import os
import typing as t
from abc import ABC, abstractmethod
from pathlib import Path

from ellar.common.compatible import cached_property
from jinja2 import FileSystemLoader
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse as TemplateResponse


class ITemplateRenderingService(ABC):
    @abstractmethod
    def render_template(
        self,
        template_name: str,
        template_context: t.Dict[str, t.Any],
        background: t.Optional[BackgroundTask] = None,
        headers: t.Union[t.Mapping[str, str], None] = None,
        status_code: int = 200,
        response_type: t.Type[TemplateResponse] = TemplateResponse,
    ) -> TemplateResponse:
        """Renders a template from the template folder with the given context.
        :param status_code: Template Response status code
        :param template_name: the name of the template to be rendered
        :param headers: Response headers
        :param response_type: Response Class.
        Default: `ellar.common.templating.TemplateResponse`
        :param template_context: variables that should be available in the context of the template.
        :param background: Any background task to be executed after render.
        :return TemplateResponse
        """

    @abstractmethod
    def render_template_string(
        self, template_string: str, **template_context: t.Any
    ) -> str:
        """Renders a template to string.
        :param template_string: Template String
        :param template_context: variables that should be available in the context of the template.
        """


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
