import typing as t
from starletteapi.types import T
from starletteapi.events import Event


class ModuleEvent(Event[t.Callable]):
    pass


class ApplicationEvent(Event[t.Callable[..., None]]):
    def __iadd__(self, handler: T) -> "ApplicationEvent":
        super(ApplicationEvent, self).__iadd__(handler)
        if handler.is_coroutine:
            raise Exception('coroutine handlers is not supported')
        return self
