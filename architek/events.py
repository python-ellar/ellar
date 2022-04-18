import asyncio
import typing as t

from architek.types import T


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
            _other = self.__class__(other)
            return self.handler is _other.handler
        return super(EventHandler, self).__eq__(other)


class ApplicationEventHandler:
    __slots__ = ("is_coroutine", "handler")

    def __init__(self, func: t.Callable) -> None:
        if asyncio.iscoroutinefunction(func):
            raise Exception("ApplicationEventHandler must be a non coroutine function")
        self.handler = func

    def run(self, **kwargs: t.Any) -> None:
        self.handler(**kwargs)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ApplicationEventHandler):
            return self.handler is other.handler
        if callable(other):
            _other = self.__class__(other)
            return self.handler is _other.handler
        return super(ApplicationEventHandler, self).__eq__(other)


class Event(t.Generic[T]):
    __slots__ = ("_handlers",)

    def __init__(self) -> None:
        self._handlers: t.List[T] = []

    def __iadd__(self, handler: t.Callable) -> "Event[T]":
        event_handler = self._create_handle(handler)
        self._handlers.append(event_handler)
        return self

    def _create_handle(self, handler: t.Callable) -> T:
        raise NotImplementedError

    def __iter__(self) -> t.Iterator[T]:
        return iter(self._handlers)

    def __isub__(self, handler: t.Callable) -> "Event[T]":
        _handler = self._create_handle(handler)
        self._handlers.remove(_handler)
        return self

    def __len__(self) -> int:
        return len(self._handlers)

    def __call__(self, handler: t.Callable) -> t.Callable:
        self.__iadd__(handler)
        return handler


class ApplicationEventManager(Event[ApplicationEventHandler]):
    def _create_handle(self, handler: t.Callable) -> ApplicationEventHandler:
        return ApplicationEventHandler(handler)

    def __init__(
        self, handlers: t.Optional[t.List[ApplicationEventHandler]] = None
    ) -> None:
        super().__init__()
        self._handlers = handlers or []

    def run(self, **kwargs: t.Any) -> None:
        for handler in self:
            handler.run(**kwargs)


class RouterEventManager(Event[EventHandler]):
    def _create_handle(self, handler: t.Callable) -> EventHandler:
        return EventHandler(handler)

    def __init__(self, handlers: t.Optional[t.List[EventHandler]] = None) -> None:
        super().__init__()
        self._handlers = handlers or []

    def reload(self, handlers: t.List[EventHandler]) -> None:
        self._handlers = handlers

    async def async_run(self) -> None:
        for handler in self:
            await handler.run()
