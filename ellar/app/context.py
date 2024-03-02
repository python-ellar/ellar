import os
import typing as t
from contextvars import ContextVar
from types import TracebackType

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.common.logging import logger
from ellar.core import Config
from ellar.di import EllarInjector
from ellar.events import app_context_started, app_context_teardown
from ellar.utils.functional import SimpleLazyObject, empty

if t.TYPE_CHECKING:
    from ellar.app.main import App

injector_context_var: ContextVar[t.Optional[t.Union["ApplicationContext", t.Any]]] = (
    ContextVar("ellar.app.context")
)


class ApplicationContext:
    """
    Makes DI container available to resolve services, Application instance and more
    when running CLI commands, serving request and others.
    """

    __slots__ = ("_injector", "_reset_token")

    def __init__(self, injector: EllarInjector) -> None:
        assert isinstance(
            injector, EllarInjector
        ), "injector must instance of EllarInjector"

        self._injector = injector
        self._reset_token = injector_context_var.set(empty)

    @property
    def injector(self) -> EllarInjector:
        return self._injector

    async def __aenter__(self) -> "ApplicationContext":
        injector_context = injector_context_var.get(empty)
        if injector_context is empty:
            # If injector_context exist
            self._reset_token = injector_context_var.set(self)

            if config._wrapped is not empty:  # pragma: no cover
                # ensure current_config is in sync with running application context.
                config._wrapped = self.injector.get(Config)

            await app_context_started.run()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Any],
        exc_value: t.Optional[BaseException],
        tb: t.Optional[TracebackType],
    ) -> None:
        injector_context_var.reset(self._reset_token)

        current_injector._wrapped = injector_context_var.get(empty)  # type:ignore[attr-defined]
        config._wrapped = injector_context_var.get(empty)

        await app_context_teardown.run()

    @classmethod
    def create(cls, app: "App") -> "ApplicationContext":
        return cls(app.injector)


def _get_injector() -> EllarInjector:
    injector_context = injector_context_var.get(empty)
    if injector_context is empty:
        raise RuntimeError("ApplicationContext is not available at this scope.")

    return injector_context.injector  # type:ignore[union-attr]


def _get_application_config() -> Config:
    injector_context = injector_context_var.get(empty)
    if injector_context is empty:
        config_module = os.environ.get(ELLAR_CONFIG_MODULE)
        if not config_module:
            logger.warning(
                "You are trying to access app config outside app context "
                "and %s is not specified. This may cause differences in config "
                "values with the app" % (ELLAR_CONFIG_MODULE,)
            )
        return Config(config_module=config_module)

    return injector_context.injector.get(Config)  # type:ignore


config: Config = t.cast(Config, SimpleLazyObject(func=_get_application_config))

current_injector: EllarInjector = t.cast(
    EllarInjector, SimpleLazyObject(func=_get_injector)
)
