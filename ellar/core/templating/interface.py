import json
import os
import typing as t
from abc import ABC, ABCMeta, abstractmethod
from pathlib import Path

from jinja2 import Environment as BaseEnvironment, FileSystemLoader
from starlette.templating import pass_context

from ellar.compatible import cached_property
from ellar.constants import TEMPLATE_FILTER_KEY, TEMPLATE_GLOBAL_KEY
from ellar.core.connection import Request
from ellar.core.staticfiles import StaticFiles
from ellar.types import ASGIApp, TemplateFilterCallable, TemplateGlobalCallable

from ..conf import Config
from .environment import Environment
from .loader import JinjaLoader

if t.TYPE_CHECKING:  # pragma: no cover
    from ellar.core.main import App
    from ellar.di import EllarInjector


class TemplateFunctionData(t.NamedTuple):
    func: t.Callable
    name: t.Optional[str]


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


class AppTemplating(JinjaTemplating):
    config: Config
    _static_app: t.Optional[ASGIApp]
    _injector: "EllarInjector"
    has_static_files: bool

    @abstractmethod
    def build_middleware_stack(self) -> t.Callable:  # pragma: no cover
        pass

    @abstractmethod
    def rebuild_middleware_stack(self) -> None:  # pragma: no cover
        pass

    def get_module_loaders(self) -> t.Generator[ModuleTemplating, None, None]:
        for loader in self._injector.get_templating_modules().values():
            yield loader

    @property
    def debug(self) -> bool:
        return self.config.DEBUG

    @debug.setter
    def debug(self, value: bool) -> None:
        del self.__dict__["jinja_environment"]
        self.config.DEBUG = value
        # TODO: Add warning
        self.rebuild_middleware_stack()

    @cached_property
    def jinja_environment(self) -> BaseEnvironment:
        _jinja_env = self._create_jinja_environment()
        self._update_jinja_env_filters(_jinja_env)
        return _jinja_env

    def _create_jinja_environment(self) -> Environment:
        def select_jinja_auto_escape(filename: str) -> bool:
            if filename is None:  # pragma: no cover
                return True
            return filename.endswith((".html", ".htm", ".xml", ".xhtml"))

        options_defaults: t.Dict = dict(
            extensions=[], auto_reload=self.debug, autoescape=select_jinja_auto_escape
        )
        jinja_options: t.Dict = t.cast(
            t.Dict, self.config.JINJA_TEMPLATES_OPTIONS or {}
        )

        for k, v in options_defaults.items():
            jinja_options.setdefault(k, v)

        @pass_context
        def url_for(context: dict, name: str, **path_params: t.Any) -> str:
            request = t.cast(Request, context["request"])
            return request.url_for(name, **path_params)

        app: App = t.cast("App", self)

        jinja_env = Environment(app, **jinja_options)
        jinja_env.globals.update(
            url_for=url_for,
            config=self.config,
        )
        jinja_env.policies["json.dumps_function"] = json.dumps
        return jinja_env

    def create_global_jinja_loader(self) -> JinjaLoader:
        return JinjaLoader(t.cast("App", self))

    def create_static_app(self) -> ASGIApp:
        return StaticFiles(
            directories=self.static_files, packages=self.config.STATIC_FOLDER_PACKAGES
        )

    def reload_static_app(self) -> None:
        del self.__dict__["static_files"]
        if self.has_static_files:
            self._static_app = self.create_static_app()
        self._update_jinja_env_filters(self.jinja_environment)

    def _update_jinja_env_filters(self, jinja_environment: Environment) -> None:
        jinja_environment.globals.update(self.config.get(TEMPLATE_GLOBAL_KEY, {}))
        jinja_environment.filters.update(self.config.get(TEMPLATE_FILTER_KEY, {}))

    @cached_property
    def static_files(self) -> t.List[str]:
        static_directories = t.cast(t.List, self.config.STATIC_DIRECTORIES or [])
        for module in self.get_module_loaders():
            if module.static_directory:
                static_directories.append(module.static_directory)
        return static_directories
