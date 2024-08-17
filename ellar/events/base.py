import typing as t
from abc import abstractmethod
from weakref import WeakKeyDictionary

T = t.TypeVar("T")


class EventHandler:
    __slots__ = ("is_coroutine", "handler")

    def __init__(self, func: t.Callable) -> None:
        self.handler = func

    async def run(self, *args: t.Any, **kwargs: t.Any) -> None:
        res = self.handler(*args, **kwargs)
        if isinstance(res, t.Coroutine):
            await res

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EventHandler):
            return self.handler is other.handler
        if callable(other):
            return self.handler is other
        return super(EventHandler, self).__eq__(other)


class EventBase(t.Generic[T]):
    __slots__ = ("_handlers",)

    def __init__(self) -> None:
        self._handlers: WeakKeyDictionary[t.Any, T] = WeakKeyDictionary()

    def __iadd__(self, handler: t.Callable) -> "EventBase[T]":
        event_handler = self.create_handle(handler)
        self._handlers[handler] = event_handler
        return self

    @abstractmethod
    def create_handle(self, handler: t.Callable) -> T:  # pragma: no cover
        pass

    def __iter__(self) -> t.Iterator[T]:
        return iter(self._handlers.values())

    def __isub__(self, handler: t.Callable) -> "EventBase[T]":
        self._handlers.pop(handler, None)
        return self

    def __len__(self) -> int:
        return len(self._handlers)

    def connect(self, handler: t.Callable) -> t.Callable:
        self.__iadd__(handler)
        return handler

    def disconnect(self, handler: t.Callable) -> t.Callable:
        self.__isub__(handler)
        return handler


class EventManager(EventBase[EventHandler]):
    def create_handle(self, handler: t.Callable) -> EventHandler:
        return EventHandler(handler)

    async def run(self, *args: t.Any, **kwargs: t.Any) -> None:
        for handler in self:
            await handler.run(*args, **kwargs)

    def disconnect_all(self) -> None:
        for handle in list(self):
            self.disconnect(handle.handler)
