import typing as t
from contextlib import asynccontextmanager

from ellar.common import IApplicationShutdown, IApplicationStartup
from ellar.common.logging import logger

if t.TYPE_CHECKING:
    from ellar.app import App

_T = t.TypeVar("_T")


@asynccontextmanager
async def _default_lifespan_context(app: "App") -> t.AsyncIterator[t.Any]:
    yield {}


class EllarApplicationLifespan:
    __slots__ = ("_lifespan_context",)

    def __init__(
        self,
        lifespan_context: t.Optional[
            t.Callable[[t.Any], t.AsyncIterator[t.Any]]
        ] = None,
    ) -> None:
        self._lifespan_context = (
            _default_lifespan_context if lifespan_context is None else lifespan_context
        )

    def _get_startup_modules(self, app: "App") -> t.Iterator[IApplicationStartup]:
        for module, _ in app.injector.tree_manager.modules.items():
            if issubclass(module, IApplicationStartup):
                yield app.injector.get(module)

    def _get_shutdown_modules(self, app: "App") -> t.Iterator[IApplicationShutdown]:
        for module, _ in app.injector.tree_manager.modules.items():
            if issubclass(module, IApplicationShutdown):
                yield app.injector.get(module)

    async def run_all_startup_actions(self, app: "App") -> None:
        try:
            for module in self._get_startup_modules(app):
                await module.on_startup(app)
        except Exception as ex:  # pragma: no cover
            logger.exception(ex.exceptions if hasattr(ex, "exceptions") else ex)
            raise ex

    async def run_all_shutdown_actions(self, app: "App") -> None:
        try:
            for module in self._get_shutdown_modules(app):
                await module.on_shutdown()
        except Exception as ex:  # pragma: no cover
            logger.exception(ex.exceptions if hasattr(ex, "exceptions") else ex)
            raise ex

    @asynccontextmanager
    async def lifespan(self, app: "App") -> t.AsyncIterator[t.Any]:
        try:
            logger.debug("Executing Modules Startup Handlers")
            await self.run_all_startup_actions(app)

            async with self._lifespan_context(app) as ctx:  # type:ignore[attr-defined]
                logger.info("Application is ready.")
                yield ctx
        finally:
            logger.debug("Executing Modules Shutdown Handlers")
            await self.run_all_shutdown_actions(app)

            logger.info("Application shutdown successfully.")
