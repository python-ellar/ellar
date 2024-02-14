import typing as t
from abc import ABC, abstractmethod


class IDocumentationUI(ABC):
    """
    Provides Templating Context and information about the OPENAPI Docs renderer.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Document UI name eg. Swagger, Redoc, Stoplight"""

    @property
    @abstractmethod
    def path(self) -> str:
        """Prefer document path"""

    @property
    @abstractmethod
    def template_name(self) -> t.Optional[str]:
        """
        OPENAPI Document UI HTML name. This will be searched for in html folders registered in your Ellar Application.
        If None is returned, OpenAPIModule will switch to inline template rendering provided in `template_string`
        """

    @property
    def template_string(self) -> t.Optional[str]:
        """
        Templated HTML string for the OPENAPI document rendering UI
        :return: Templated String or None
        """
        return None  # pragma: no cover

    @property
    @abstractmethod
    def template_context(self) -> dict:
        """Other Document manger settings that will be passed to the template"""
