import os.path
import typing as t

from ellar.common.types import ASGIApp
from ellar.core.staticfiles import StaticFiles
from ellar.utils.importer import get_main_directory_by_stack
from starlette.middleware import Middleware
from starlette.routing import BaseRoute, Mount

if t.TYPE_CHECKING:
    from ellar.app import App


class ASGIFileMount(Mount):
    def __init__(
        self,
        directories: t.Sequence[str],
        path: str,
        name: str,
        packages: t.Optional[t.List[t.Union[str, t.Tuple[str, str]]]] = None,
        middleware: t.Optional[t.Sequence[Middleware]] = None,
        base_directory: t.Optional[str] = None,
    ) -> None:
        base_directory = get_main_directory_by_stack(base_directory, stack_level=2)  # type: ignore[arg-type]
        if base_directory:
            directories = [
                str(os.path.join(base_directory, directory))
                for directory in directories
            ]

        self._middleware = middleware

        _files_app = StaticFiles(directories=directories, packages=packages)  # type:ignore[arg-type]
        super().__init__(
            path=path, name=name, app=self._combine_app_with_middleware(_files_app)
        )

    def _combine_app_with_middleware(self, app: ASGIApp) -> ASGIApp:
        if self._middleware is not None:
            for cls, _, kwargs in reversed(self._middleware):
                app = cls(app=app, **kwargs)
        return app

    @property
    def routes(self) -> t.List[BaseRoute]:
        return []


class AppStaticFileMount(ASGIFileMount):
    def __init__(self, app: "App") -> None:
        directories, packages = self._get_static_directories(app)
        assert app.config.STATIC_MOUNT_PATH
        super().__init__(
            path=app.config.STATIC_MOUNT_PATH,
            name="static",
            directories=directories,
            packages=packages,
        )
        # subscribe to app reload

    def _get_static_directories(self, app: "App") -> tuple:
        static_directories = t.cast(t.List, app.config.STATIC_DIRECTORIES or [])
        for module in app.get_module_loaders():
            if module.static_directory:
                static_directories.append(module.static_directory)
        return static_directories, app.config.STATIC_FOLDER_PACKAGES

    # def _reload_static_files(self, app: "App") -> None:
    #     directories, packages = self._get_static_directories(app)
    #     self.app = self._combine_app_with_middleware(
    #         StaticFiles(directories=directories, packages=packages)
    #     )
