from abc import ABC, abstractmethod


class IDocumentationGenerator(ABC):
    @property
    @abstractmethod
    def title(self) -> str:
        """Page Title"""

    @property
    @abstractmethod
    def path(self) -> str:
        """Prefer document path"""

    @property
    @abstractmethod
    def template_name(self) -> str:
        """Document Manager Template Name"""

    @property
    @abstractmethod
    def template_context(self) -> dict:
        """Other Document manger settings that will be passed to the template"""
