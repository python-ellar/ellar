import asyncio
import typing as t
from abc import abstractmethod

from ellar.common.types import T


class EventHandler:
    __slots__ = ("is_coroutine", "handler")

    def __init__(self, func: t.Callable) -> None:
        self.is_coroutine = asyncio.iscoroutinefunction(func)
        self.handler = func

    async def run(self) -> None:
        if self.is_coroutine:
            await self.handler()
            return
        self.handler()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EventHandler):
            return self.handler is other.handler
        if callable(other):
            return self.handler is other
        return super(EventHandler, self).__eq__(other)


class Event(t.Generic[T]):
    __slots__ = ("_handlers",)

    def __init__(self) -> None:
        self._handlers: t.List[T] = []

    def __iadd__(self, handler: t.Callable) -> "Event[T]":
        event_handler = self.create_handle(handler)
        self._handlers.append(event_handler)
        return self

    @abstractmethod
    def create_handle(self, handler: t.Callable) -> T:  # pragma: no cover
        pass

    def __iter__(self) -> t.Iterator[T]:
        return iter(self._handlers)

    def __isub__(self, handler: t.Callable) -> "Event[T]":
        _handler = self.create_handle(handler)
        self._handlers.remove(_handler)
        return self

    def __len__(self) -> int:
        return len(self._handlers)

    def __call__(self, handler: t.Callable) -> t.Callable:
        self.__iadd__(handler)
        return handler


class RouterEventManager(Event[EventHandler]):
    def create_handle(self, handler: t.Callable) -> EventHandler:
        return EventHandler(handler)

    def __init__(self, handlers: t.Optional[t.List[EventHandler]] = None) -> None:
        super().__init__()
        self._handlers = handlers or []

    def reload(self, handlers: t.List[EventHandler]) -> None:
        self._handlers = handlers

    async def async_run(self) -> None:
        for handler in self:
            await handler.run()
