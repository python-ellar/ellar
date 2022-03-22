import asyncio
import typing as t
from starletteapi.types import T


class Event(t.Generic[T]):
    __slots__ = ('_handlers',)

    def __init__(self) -> None:
        self._handlers: t.List[T] = []

    def __iadd__(self, handler: T) -> "Event[T]":
        self._handlers.append(handler)
        handler.is_coroutine = asyncio.iscoroutinefunction(handler)
        return self

    def __iter__(self):
        return iter(self._handlers)

    def __isub__(self, handler: T) -> "Event[T]":
        self._handlers.remove(handler)
        return self

    def __len__(self) -> int:
        return len(self._handlers)

    def __call__(self, handler: T):
        self._handlers.append(handler)
        handler.is_coroutine = asyncio.iscoroutinefunction(handler)
        return handler


class ApplicationEventManager(Event[t.Callable]):
    def __init__(self, handlers: t.List[t.Callable]):
        super().__init__()
        self._handlers = handlers

    def run(self, **kwargs: t.Any):
        for handler in self:
            handler(**kwargs)

    def __iadd__(self, other) -> 'ApplicationEventManager':
        return self


class RouterEventManager(Event[t.Callable]):
    def __init__(self, handlers: t.List[t.Callable]):
        super().__init__()
        self._handlers = handlers

    def reload(self, handlers: t.List[t.Callable]):
        self._handlers = handlers

    async def async_run(self):
        for handler in self:
            if handler.is_coroutine:
                await handler()
                continue
            handler()
