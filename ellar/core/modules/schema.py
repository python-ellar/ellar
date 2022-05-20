import typing as t

from starlette.middleware import Middleware
from starlette.routing import BaseRoute

from ellar.core.events import ApplicationEventHandler, EventHandler


class ModuleData(t.NamedTuple):
    before_init: t.List[ApplicationEventHandler]
    after_init: t.List[ApplicationEventHandler]
    startup_event: t.List[EventHandler]
    shutdown_event: t.List[EventHandler]
    exception_handlers: t.Dict
    middleware: t.List[Middleware]
    routes: t.List[BaseRoute]
