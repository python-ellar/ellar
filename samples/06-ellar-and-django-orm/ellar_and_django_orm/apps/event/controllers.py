"""
Define endpoints routes in python class-based fashion
example:

@Controller("/dogs", tag="Dogs", description="Dogs Resources")
class MyController(ControllerBase):
    @get('/')
    def index(self):
        return {'detail': "Welcome Dog's Resources"}
"""

import typing as t

from ellar.common import Controller, ControllerBase, get, post

from ...interfaces.events_repository import IEventRepository
from .schemas import EventSchemaIn, EventSchemaOut


@Controller("/event")
class EventController(ControllerBase):
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    @post("/", response={201: EventSchemaOut})
    def create_event(self, event: EventSchemaIn):
        event = self.event_repo.create_event(**event.dict())
        return 201, event

    @get("/", response=t.List[EventSchemaOut], name="event-list")
    def list_events(self):
        return list(self.event_repo.list_events())

    @get("/{event_id:int}", response=EventSchemaOut, name="event-detail")
    def get_event_by_id(self, event_id: int):
        return self.event_repo.get_by_id(event_id)
