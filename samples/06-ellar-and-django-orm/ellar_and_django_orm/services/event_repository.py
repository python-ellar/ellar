import typing as t
from datetime import datetime, timedelta

import ellar.common as ec
from ellar.di import injectable

from ..interfaces.dto import EventDTO
from ..interfaces.events_repository import IEventRepository
from ..wsgi_django.db_models.models import Event


@injectable
class EventRepository(IEventRepository):
    _dummy_data = {
        "title": "TestEvent1Title",
        "start_date": str(datetime.now().date()),
        "end_date": str((datetime.now() + timedelta(days=5)).date()),
    }

    def _seed(self) -> None:
        if not Event.objects.exists():
            for i in range(10):
                object_data = self._dummy_data.copy()
                object_data.update(title=f"{object_data['title']}_{i + 1}")
                Event.objects.create(**object_data)

    def create_event(self, **kwargs: t.Dict) -> EventDTO:
        event = Event.objects.create(**kwargs)
        return EventDTO.from_orm(event)

    def list_events(self) -> t.List[EventDTO]:
        self._seed()
        return [EventDTO.from_orm(event) for event in Event.objects.all()]

    def get_by_id(self, event_id: t.Any) -> EventDTO:
        event = Event.objects.filter(id=event_id).first()
        if not event:
            raise ec.NotFound()
        return EventDTO.from_orm(event)
