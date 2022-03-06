import json
import os
import typing as t
from abc import abstractmethod
from jinja2 import FileSystemLoader
from starlette.templating import pass_context

from starletteapi.types import ASGIApp, TemplateGlobalCallable, TemplateFilterCallable
from .environment import Environment
from ..compatible import locked_cached_property, cached_property
from .loader import StarletteJinjaLoader
from ..conf import Config
from ..static_files import StarletteStaticFiles

if t.TYPE_CHECKING:
    from ..module import ApplicationModule


class JinjaTemplating:
    @property
    @abstractmethod
    def template_folder(self) -> t.Optional[str]:
        ...

    @property
    @abstractmethod
    def root_path(self) -> t.Optional[str]:
        ...

    @locked_cached_property
    def jinja_loader(self) -> t.Optional[FileSystemLoader]:
        if self.template_folder and self.root_path:
            return FileSystemLoader(os.path.join(str(self.root_path), self.template_folder))
        else:
            return None


class ModuleTemplating(JinjaTemplating):
    _template_folder: t.Optional[str]
    _module_base_directory: t.Optional[str]
    _static_folder: t.Optional[str]

    @property
    def template_folder(self) -> t.Optional[str]:
        return self._template_folder

    @property
    def root_path(self) -> t.Optional[str]:
        return self._module_base_directory

    @cached_property
    def static_directory(self) -> t.Optional[str]:
        if self.root_path and self._static_folder:
            path = os.path.join(str(self.root_path), self._static_folder)
            if os.path.exists(path):
                return path
        return None


class StarletteAppTemplating:
    config: Config
    _static_app: t.Optional[ASGIApp]
    _debug: bool
    _app_module: 'ApplicationModule'
    has_static_files: bool

    def get_module_loaders(self) -> t.Generator[ModuleTemplating, None, None]:

        for loader in self._app_module.modules():
            yield loader

    @locked_cached_property
    def jinja_environment(self) -> Environment:
        _jinja_env = self._create_jinja_environment()
        return _jinja_env

    def _create_jinja_environment(self) -> Environment:
        def select_jinja_auto_escape(filename: str) -> bool:
            if filename is None:
                return True
            return filename.endswith((".html", ".htm", ".xml", ".xhtml"))

        # TODO: get extensions from configuration
        options = dict(extensions=[])

        _auto_reload = self.config.TEMPLATES_AUTO_RELOAD
        _auto_reload = _auto_reload if _auto_reload is not None else self._debug

        if "autoescape" not in options:
            options["autoescape"] = select_jinja_auto_escape

        if "auto_reload" not in options:
            options["auto_reload"] = _auto_reload

        @pass_context
        def url_for(context: dict, name: str, **path_params: t.Any) -> str:
            request = context["request"]
            return request.url_for(name, **path_params)

        jinja_env = Environment(t.cast('StarletteApp', self), **options)
        jinja_env.globals.update(
            url_for=url_for,
            config=self.config,
        )
        jinja_env.policies["json.dumps_function"] = json.dumps
        return jinja_env

    def create_global_jinja_loader(self) -> StarletteJinjaLoader:
        return StarletteJinjaLoader(t.cast('StarletteApp', self))

    def create_static_app(self) -> ASGIApp:
        return StarletteStaticFiles(
            directories=self.static_files, packages=self.config.validate_config.STATIC_FOLDER_PACKAGES
        )

    def reload_static_app(self) -> None:
        del self.__dict__['static_files']
        if self.has_static_files:
            self._static_app = self.create_static_app()

    @cached_property
    def static_files(self) -> t.List[str]:
        static_directories = []
        for module in self.get_module_loaders():
            if module.static_directory:
                static_directories.append(module.static_directory)
        return static_directories

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
