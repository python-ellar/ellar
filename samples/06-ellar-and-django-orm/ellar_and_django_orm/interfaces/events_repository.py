import typing as t
from abc import abstractmethod

from .dto import EventDTO


class IEventRepository:
    @abstractmethod
    def create_event(self, **kwargs: t.Dict) -> EventDTO:
        pass

    @abstractmethod
    def list_events(self) -> t.List[EventDTO]:
        pass

    @abstractmethod
    def get_by_id(self, event_id: t.Any) -> EventDTO:
        pass
