import os
import typing as t
from contextlib import asynccontextmanager
from contextvars import ContextVar

from ellar.common.constants import ELLAR_CONFIG_MODULE
from ellar.common.logging import logger
from ellar.core.conf import Config
from ellar.di import EllarInjector
from ellar.utils.functional import SimpleLazyObject, empty

_injector_context_var: ContextVar[EllarInjector] = ContextVar("ellar.di.EllarInjector")
_injector_context_var.set(empty)


def _get_injector() -> EllarInjector:
    injector_ctx = _injector_context_var.get()
    if injector_ctx is empty:
        raise RuntimeError("ApplicationContext is not available at this scope.")
    return injector_ctx


def _get_application_config() -> Config:
    injector_ctx = _injector_context_var.get()
    if injector_ctx is not empty:
        return t.cast(Config, injector_ctx.get(Config))

    config_module = os.environ.get(ELLAR_CONFIG_MODULE)
    if not config_module:
        logger.warning(
            "You are trying to access app config outside app context "
            "and %s is not specified. This may cause differences in config "
            "values with the app" % (ELLAR_CONFIG_MODULE,)
        )

    return Config(config_module=config_module)


current_config: Config = t.cast(Config, SimpleLazyObject(func=_get_application_config))

current_injector: EllarInjector = t.cast(
    EllarInjector, SimpleLazyObject(func=_get_injector)
)


def _clear_lazy_objects() -> None:
    current_injector._wrapped = empty  # type:ignore[attr-defined]
    current_config._wrapped = empty


@asynccontextmanager
async def injector_context(
    injector: EllarInjector,
) -> t.AsyncGenerator[EllarInjector, t.Any]:
    _clear_lazy_objects()
    _injector_reset_token = _injector_context_var.set(injector)

    yield injector

    _injector_context_var.reset(_injector_reset_token)
    _clear_lazy_objects()
