import os
import stat
import typing as t

import anyio
from starlette.staticfiles import PathLike, StaticFiles as StarletteStaticFiles


class StaticFiles(StarletteStaticFiles):
    def __init__(
        self,
        *,
        directories: t.List[PathLike] = None,
        packages: t.List[t.Union[str, t.Tuple[str, str]]] = None,
        html: bool = False,  # TODO: expose to config
        check_dir: bool = True,  # TODO: expose to config
    ):
        super(StaticFiles, self).__init__(
            html=html, packages=packages, check_dir=check_dir
        )
        self._directories = [] if directories is None else list(directories)
        self.all_directories.extend(self._directories)

        if check_dir:
            for directory in self._directories:
                if not os.path.isdir(directory):
                    raise RuntimeError(f"Directory '{directory}' does not exist")

    async def check_config(self) -> None:
        """
        Perform a one-off configuration check that StaticFiles is actually
        pointed at a directory, so that we can raise loud errors rather than
        just returning 404 responses.
        """
        for directory in self._directories:
            try:
                stat_result = await anyio.to_thread.run_sync(os.stat, directory)
            except FileNotFoundError:
                raise RuntimeError(
                    f"StaticFiles directory '{directory}' does not exist."
                )
            if not (
                stat.S_ISDIR(stat_result.st_mode) or stat.S_ISLNK(stat_result.st_mode)
            ):
                raise RuntimeError(
                    f"StaticFiles path '{directory}' is not a directory."
                )
