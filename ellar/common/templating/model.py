import os
import typing as t
from abc import ABC, ABCMeta
from pathlib import Path

from ellar.common.compatible import cached_property
from ellar.common.interfaces import IModuleTemplateLoader
from ellar.common.types import TemplateFilterCallable, TemplateGlobalCallable
from jinja2 import Environment as BaseEnvironment


class JinjaTemplating(ABC, metaclass=ABCMeta):
    jinja_environment: BaseEnvironment

    def template_filter(
        self, name: t.Optional[str] = None
    ) -> t.Callable[[TemplateFilterCallable], TemplateFilterCallable]:
        """A decorator that is used to register custom template filter.
        You can specify a name for the filter, otherwise the function
        name will be used. Example::

          @app.template_filter()
          def reverse(s):
              return s[::-1]

        :param name: the optional name of the filter, otherwise the
                     function name will be used.
        """

        def decorator(f: TemplateFilterCallable) -> TemplateFilterCallable:
            self.add_template_filter(f, name=name)
            return f

        return decorator

    def add_template_filter(
        self, f: TemplateFilterCallable, name: t.Optional[str] = None
    ) -> None:
        self.jinja_environment.filters[name or f.__name__] = f

    def template_global(
        self, name: t.Optional[str] = None
    ) -> t.Callable[[TemplateGlobalCallable], TemplateGlobalCallable]:
        """A decorator that is used to register a custom template global function.
        You can specify a name for the global function, otherwise the function
        name will be used. Example::

            @app.template_global()
            def double(n):
                return 2 * n

        :param name: the optional name of the global function, otherwise the
                     function name will be used.
        """

        def decorator(f: TemplateGlobalCallable) -> TemplateGlobalCallable:
            self.add_template_global(f, name=name)
            return f

        return decorator

    def add_template_global(
        self, f: TemplateGlobalCallable, name: t.Optional[str] = None
    ) -> None:
        self.jinja_environment.globals[name or f.__name__] = f


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
