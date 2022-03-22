import typing
from starlette.staticfiles import StaticFiles, PathLike


class StarletteStaticFiles(StaticFiles):
    def __init__(
        self,
        *,
        directories: typing.List[PathLike],
        packages: typing.List[typing.Union[str, typing.Tuple[str, str]]] = None,
        html: bool = False,  # TODO: expose to config
        check_dir: bool = True,  # TODO: expose to config
    ):
        super(StarletteStaticFiles, self).__init__(
            html=html, packages=packages, check_dir=check_dir
        )
        self.all_directories.extend(directories)
