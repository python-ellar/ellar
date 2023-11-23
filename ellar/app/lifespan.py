import typing as t

from anyio import create_task_group
from ellar.common import IApplicationShutdown, IApplicationStartup
from ellar.common.logger import logger
from ellar.reflect import asynccontextmanager

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
        for module, module_ref in app.injector.get_modules().items():
            module_ref.run_module_register_services()
            if issubclass(module, IApplicationStartup):
                yield app.injector.get(module)

    def _get_shutdown_modules(self, app: "App") -> t.Iterator[IApplicationShutdown]:
        for module in app.injector.get_modules():
            if issubclass(module, IApplicationShutdown):
                yield app.injector.get(module)

    async def run_all_startup_actions(self, app: "App") -> None:
        async with create_task_group() as tg:
            for module in self._get_startup_modules(app):
                tg.start_soon(module.on_startup, app)

    async def run_all_shutdown_actions(self, app: "App") -> None:
        async with create_task_group() as tg:
            for module in self._get_shutdown_modules(app):
                tg.start_soon(module.on_shutdown)

    @asynccontextmanager
    async def lifespan(self, app: "App") -> t.AsyncIterator[t.Any]:
        logger.debug("Executing Modules Startup Handlers")

        async with create_task_group() as tg:
            tg.start_soon(self.run_all_startup_actions, app)

        try:
            async with self._lifespan_context(app) as ctx:  # type:ignore[attr-defined]
                logger.info("Application is ready.")
                yield ctx
        finally:
            logger.debug("Executing Modules Shutdown Handlers")
            async with create_task_group() as tg:
                tg.start_soon(self.run_all_shutdown_actions, app)
            logger.info("Application shutdown successfully.")
